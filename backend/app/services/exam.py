from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.omr_layouts import resolve_layout_version
from app.models.attempt import Attempt, AttemptAnswer
from app.models.class_ import Class, ClassStudent, TeacherClass
from app.models.enums import ExamStatus
from app.models.exam import Exam, ExamClass
from app.models.user import User
from app.repositories.attempt import AttemptRepository
from app.repositories.exam import ExamRepository
from app.repositories.grade import GradeRepository
from app.repositories.omr import OMRScanRepository, OMRTemplateRepository
from app.repositories.skill import SkillRepository
from app.schemas.exam import ExamCreate, ExamUpdate
from app.schemas.omr import OMRTemplateCreate
from app.services.answer_key import AnswerKeyService
from app.services.audit_log import AuditLogService
from app.services.export import ExportService


class ExamService:
    def __init__(self, db: Session):
        self.db = db
        self.exam_repo = ExamRepository(db)
        self.attempt_repo = AttemptRepository(db)
        self.template_repo = OMRTemplateRepository(db)
        self.scan_repo = OMRScanRepository(db)
        self.grade_repo = GradeRepository(db)
        self.skill_repo = SkillRepository(db)
        self.answer_key_service = AnswerKeyService(db)
        self.audit_log_service = AuditLogService(db)

    @staticmethod
    def _normalize_class_ids(class_ids: list[UUID] | None) -> list[UUID]:
        if class_ids is None:
            return []
        return list(dict.fromkeys(class_ids))

    def _load_classes(self, class_ids: list[UUID]) -> list[Class]:
        if not class_ids:
            return []
        classes = self.db.query(Class).filter(Class.id.in_(class_ids)).all()
        class_by_id = {class_obj.id: class_obj for class_obj in classes}
        missing_ids = [class_id for class_id in class_ids if class_id not in class_by_id]
        if missing_ids:
            raise ValueError(f"Class {missing_ids[0]} not found.")
        return [class_by_id[class_id] for class_id in class_ids]

    def _teacher_can_manage_class(
        self,
        *,
        class_obj: Class,
        teacher_id: UUID,
        can_manage_all_classes: bool,
    ) -> bool:
        if can_manage_all_classes:
            return True
        return (
            self.db.query(TeacherClass)
            .filter(
                TeacherClass.class_id == class_obj.id,
                TeacherClass.teacher_id == teacher_id,
                TeacherClass.is_active.is_(True),
            )
            .first()
            is not None
        )

    def _sync_exam_classes(
        self,
        exam: Exam,
        class_ids: list[UUID] | None,
        *,
        teacher_id: UUID,
        can_manage_all_classes: bool = False,
    ) -> None:
        if class_ids is None:
            return

        desired_class_ids = self._normalize_class_ids(class_ids)
        desired_classes = self._load_classes(desired_class_ids)

        for class_obj in desired_classes:
            if not class_obj.is_active:
                raise ValueError(f"Class {class_obj.id} not found.")
            if not self._teacher_can_manage_class(
                class_obj=class_obj,
                teacher_id=teacher_id,
                can_manage_all_classes=can_manage_all_classes,
            ):
                raise ValueError(f"Class {class_obj.id} not found.")

        existing_links = {link.class_id: link for link in exam.class_assignments}
        desired_names = [class_obj.name for class_obj in desired_classes]
        now = datetime.now(timezone.utc)

        for link in list(exam.class_assignments):
            if link.class_id not in desired_class_ids and link.is_active:
                link.is_active = False
                link.archived_at = now

        for class_obj in desired_classes:
            link = existing_links.get(class_obj.id)
            if link is None:
                self.db.add(
                    ExamClass(
                        exam_id=exam.id,
                        class_id=class_obj.id,
                        is_active=True,
                    )
                )
            else:
                link.is_active = True
                link.archived_at = None

        exam.class_id = ", ".join(desired_names) if desired_names else None
        self.audit_log_service.record(
            event_type="exam.class_assignment.sync",
            user_id=teacher_id,
            resource_type="exam",
            resource_id=exam.id,
            metadata={"class_ids": [str(class_id) for class_id in desired_class_ids]},
        )

    def _student_has_access_to_exam(self, exam: Exam, student_id: UUID) -> bool:
        active_class_ids = [link.class_id for link in exam.class_assignments if link.is_active]
        if not active_class_ids:
            return False
        return (
            self.db.query(ClassStudent.id)
            .join(Class, Class.id == ClassStudent.class_id)
            .filter(
                ClassStudent.student_id == student_id,
                ClassStudent.is_active.is_(True),
                Class.is_active.is_(True),
                ClassStudent.class_id.in_(active_class_ids),
            )
            .first()
            is not None
        )

    def create_exam(
        self,
        exam_in: ExamCreate,
        teacher_id: UUID,
        owner_id: Optional[UUID] = None,
        *,
        can_manage_all_classes: bool = False,
    ) -> Exam:
        if exam_in.questions and exam_in.correct_answers:
            raise ValueError(
                "Provide either Workflow A questions or Workflow B correct_answers, not both."
            )

        if exam_in.questions:
            exam_in.total_questions = len(exam_in.questions)

        # 1. If omr_template_id not provided, create an OMRTemplate automatically
        omr_template_id = exam_in.omr_template_id
        if omr_template_id and owner_id is not None:
            tmpl = self.template_repo.get_by_id(omr_template_id, owner_id=owner_id)
            if tmpl is None:
                raise ValueError(f"OMR Template {omr_template_id} not found.")
        if not omr_template_id and exam_in.correct_answers:
            layout_ver = exam_in.layout_version or resolve_layout_version(exam_in.total_questions)
            template_in = OMRTemplateCreate(
                layout_version=layout_ver,
                total_questions=exam_in.total_questions,
                options_per_question=5,
                correct_answers=exam_in.correct_answers,
            )
            tmpl = self.template_repo.create(template_in, created_by=teacher_id)
            omr_template_id = tmpl.id

        exam_in.omr_template_id = omr_template_id
        exam = self.exam_repo.create(exam_in, teacher_id=teacher_id)

        if exam_in.class_ids is not None:
            self._sync_exam_classes(
                exam,
                exam_in.class_ids,
                teacher_id=teacher_id,
                can_manage_all_classes=can_manage_all_classes,
            )

        # 2. Link OMRTemplate back to exam
        if omr_template_id:
            tmpl = self.template_repo.get_by_id(omr_template_id, owner_id=owner_id)
            if tmpl:
                tmpl.exam_id = exam.id
                tmpl.title = exam.title
                self.db.commit()

        # 3. Materialize Question Bank compositions into AnswerKey rows.
        if exam_in.questions:
            self.exam_repo.create_exam_questions_bulk(
                exam_id=exam.id,
                questions_in=exam_in.questions,
                created_by=teacher_id,
            )

        # 4. Materialize AnswerKey rows from the direct answer mapping.
        if exam_in.correct_answers:
            self.answer_key_service.create_from_mapping(
                exam_id=exam.id,
                correct_answers=exam_in.correct_answers,
            )

        self.db.commit()
        self.db.refresh(exam)
        return exam

    def publish_exam(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> Exam:
        exam = self._require_exam(exam_id, teacher_id=teacher_id)
        if exam.status != ExamStatus.DRAFT.value:
            raise ValueError(f"Exam {exam_id} must be draft to publish.")

        if exam.answer_key is None:
            self.answer_key_service.publish_for_exam(exam_id)
        else:
            if not exam.answer_key.items:
                raise ValueError(f"Exam {exam_id} has an empty AnswerKey.")
            self.answer_key_service.publish_answer_key(exam.answer_key.id)

        exam.status = ExamStatus.PUBLISHED.value
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def return_exam_to_draft(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> Exam:
        exam = self._require_exam(exam_id, teacher_id=teacher_id)
        if exam.status == ExamStatus.ARCHIVED.value:
            raise ValueError(f"Exam {exam_id} is archived and cannot return to draft.")

        if exam.status == ExamStatus.DRAFT.value:
            return exam

        if exam.attempts:
            raise ValueError(f"Exam {exam_id} has Attempts and cannot return to draft.")

        exam.status = ExamStatus.DRAFT.value
        exam.is_active = True
        exam.deleted_at = None
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def archive_exam(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> Exam:
        exam = self._require_exam(exam_id, teacher_id=teacher_id)
        if exam.status == ExamStatus.ARCHIVED.value:
            return exam

        exam.status = ExamStatus.ARCHIVED.value
        exam.is_active = False
        exam.deleted_at = datetime.now(timezone.utc)
        if exam.omr_template_id:
            tmpl = self.template_repo.get_by_id(exam.omr_template_id)
            if tmpl:
                tmpl.is_active = False
                tmpl.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def _require_exam(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> Exam:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")
        if teacher_id is not None and exam.teacher_id != teacher_id:
            raise ValueError(f"Exam {exam_id} not found.")
        return exam

    def get_exam(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> Optional[Exam]:
        exam = self.exam_repo.get_by_id(exam_id)
        if not exam:
            return None
        if teacher_id is not None and exam.teacher_id != teacher_id:
            return None
        return exam

    def get_exam_for_student(
        self,
        exam_id: UUID,
        student_id: Optional[UUID] = None,
    ) -> Optional[Exam]:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            return None
        if exam.status != ExamStatus.PUBLISHED.value or not exam.is_active:
            return None
        if student_id is not None and not self._student_has_access_to_exam(exam, student_id):
            raise PermissionError(
                f"Student {student_id} is not enrolled in an assigned class for exam {exam_id}."
            )
        return exam

    def list_exams(
        self, teacher_id: Optional[UUID] = None, class_id: Optional[str] = None
    ) -> List[Exam]:
        return self.exam_repo.get_all(teacher_id=teacher_id, class_id=class_id)

    def update_exam(
        self,
        exam_id: UUID,
        update_in: ExamUpdate,
        teacher_id: Optional[UUID] = None,
        can_manage_all_classes: bool = False,
    ) -> Optional[Exam]:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            return None
        if teacher_id is not None and exam.teacher_id != teacher_id:
            return None
        if exam.status == ExamStatus.ARCHIVED.value:
            raise ValueError(f"Exam {exam_id} is archived and cannot be edited.")
        updated_exam = self.exam_repo.update(exam_id, update_in)
        if updated_exam is None:
            return None
        if update_in.class_ids is not None:
            self._sync_exam_classes(
                updated_exam,
                update_in.class_ids,
                teacher_id=teacher_id or updated_exam.teacher_id,
                can_manage_all_classes=can_manage_all_classes,
            )
            self.db.commit()
            self.db.refresh(updated_exam)
        return updated_exam

    def soft_delete_exam(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> bool:
        """
        Soft deletes an exam (sets is_active=False, deleted_at=now()).
        Preserves historical Attempt, AttemptAnswer and Grade records!
        """
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            return False
        if teacher_id is not None and exam.teacher_id != teacher_id:
            return False
        self.archive_exam(exam.id, teacher_id=teacher_id)
        return True

    def soft_delete_template(self, template_id: UUID, teacher_id: Optional[UUID] = None) -> bool:
        """
        Soft deletes an OMR template (sets is_active=False, deleted_at=now()).
        Preserves OMR scans and historical grades.
        """
        tmpl = self.template_repo.get_by_id(template_id, owner_id=teacher_id)
        if not tmpl:
            return False
        tmpl.is_active = False
        tmpl.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def calculate_attempt_score(
        self,
        total_questions: int,
        correct_answers: int,
        max_score: Decimal,
    ) -> Dict[str, Any]:
        incorrect_answers = total_questions - correct_answers
        accuracy_percentage = (
            (Decimal(correct_answers) / Decimal(total_questions)) * Decimal("100.00")
            if total_questions > 0
            else Decimal("0.00")
        )
        raw_score = Decimal(correct_answers)
        final_score = (
            (Decimal(correct_answers) / Decimal(total_questions)) * max_score
            if total_questions > 0
            else Decimal("0.00")
        )
        return {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "accuracy_percentage": accuracy_percentage.quantize(Decimal("0.01")),
            "raw_score": raw_score.quantize(Decimal("0.01")),
            "final_score": final_score.quantize(Decimal("0.01")),
        }

    def get_exam_statistics(
        self,
        exam_id: UUID,
        teacher_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        exam = self._require_exam(exam_id, teacher_id=teacher_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")

        attempts = self.attempt_repo.get_by_exam_id(exam_id)
        total_attempts = len(attempts)
        answer_key_items = self.answer_key_service.get_item_map_for_exam(exam_id)

        question_stats = []
        for i in range(1, exam.total_questions + 1):
            answer_key_item = answer_key_items.get(i)
            correct_opt = answer_key_item.correct_answer if answer_key_item else None

            # Query answers for the canonical AnswerKeyItem when one exists.
            if answer_key_item:
                answers_for_q = (
                    self.db.query(AttemptAnswer)
                    .join(Attempt)
                    .filter(
                        Attempt.exam_id == exam_id,
                        AttemptAnswer.answer_key_item_id == answer_key_item.id,
                    )
                    .all()
                )
            else:
                answers_for_q = []

            total_resp = len(answers_for_q)
            correct_cnt = sum(1 for a in answers_for_q if a.is_correct)
            incorrect_cnt = total_resp - correct_cnt
            accuracy_pct = (correct_cnt / total_resp * 100.0) if total_resp > 0 else 0.0
            error_pct = (incorrect_cnt / total_resp * 100.0) if total_resp > 0 else 0.0

            q_skills = [
                {
                    "id": s.id,
                    "code": s.code,
                    "description": s.description,
                    "subject": s.subject,
                    "grade_level": s.grade_level,
                    "curriculum": s.curriculum,
                }
                for s in (answer_key_item.skills if answer_key_item else [])
            ]

            question_stats.append(
                {
                    "question_number": i,
                    "statement": answer_key_item.statement if answer_key_item else None,
                    "correct_option": correct_opt,
                    "skills": q_skills,
                    "total_responses": total_resp,
                    "correct_count": correct_cnt,
                    "incorrect_count": incorrect_cnt,
                    "accuracy_percentage": round(accuracy_pct, 2),
                    "error_percentage": round(error_pct, 2),
                }
            )

        avg_score = (
            sum(float(a.final_score) for a in attempts) / total_attempts
            if total_attempts > 0
            else 0.0
        )

        return {
            "exam_id": exam.id,
            "exam_title": exam.title,
            "total_attempts": total_attempts,
            "class_id": exam.class_id,
            "average_score": round(avg_score, 2),
            "max_score": float(exam.max_score),
            "question_statistics": question_stats,
        }

    def export_exam_pdf(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> bytes:
        exam = self._require_exam(exam_id, teacher_id=teacher_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")

        teacher = self.db.query(User).filter(User.id == exam.teacher_id).first()
        teacher_name = teacher.email if teacher else "Professor"

        stats = self.get_exam_statistics(exam_id, teacher_id=teacher_id)
        attempts_db = self.attempt_repo.get_by_exam_id(exam_id)

        attempts_list = []
        for att in attempts_db:
            st_user = (
                self.db.query(User).filter(User.id == att.student_id).first()
                if att.student_id
                else None
            )
            attempts_list.append(
                {
                    "student_code": att.student_code,
                    "student_name": (
                        st_user.email
                        if st_user
                        else f"Aluno ({att.student_code or 'Desconhecido'})"
                    ),
                    "correct_answers": att.correct_answers,
                    "accuracy_percentage": float(att.accuracy_percentage),
                    "final_score": float(att.final_score),
                }
            )

        return ExportService.generate_exam_pdf_report(
            exam_title=exam.title,
            class_id=exam.class_id or "Geral",
            teacher_name=teacher_name,
            max_score=float(exam.max_score),
            total_questions=exam.total_questions,
            attempts=attempts_list,
            question_stats=stats["question_statistics"],
        )

    def export_exam_xlsx(self, exam_id: UUID, teacher_id: Optional[UUID] = None) -> bytes:
        exam = self._require_exam(exam_id, teacher_id=teacher_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")

        teacher = self.db.query(User).filter(User.id == exam.teacher_id).first()
        teacher_name = teacher.email if teacher else "Professor"

        stats = self.get_exam_statistics(exam_id, teacher_id=teacher_id)
        attempts_db = self.attempt_repo.get_by_exam_id(exam_id)

        attempts_list = []
        for att in attempts_db:
            st_user = (
                self.db.query(User).filter(User.id == att.student_id).first()
                if att.student_id
                else None
            )
            attempts_list.append(
                {
                    "student_code": att.student_code,
                    "student_name": (
                        st_user.email
                        if st_user
                        else f"Aluno ({att.student_code or 'Desconhecido'})"
                    ),
                    "correct_answers": att.correct_answers,
                    "incorrect_answers": att.incorrect_answers,
                    "accuracy_percentage": float(att.accuracy_percentage),
                    "final_score": float(att.final_score),
                }
            )

        return ExportService.generate_exam_xlsx_report(
            exam_title=exam.title,
            class_id=exam.class_id or "Geral",
            teacher_name=teacher_name,
            max_score=float(exam.max_score),
            total_questions=exam.total_questions,
            attempts=attempts_list,
            question_stats=stats["question_statistics"],
        )
