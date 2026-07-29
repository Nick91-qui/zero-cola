from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.attempt import Attempt, AttemptAnswer
from app.models.enums import ExamStatus
from app.models.exam import Exam
from app.models.user import User
from app.repositories.attempt import AttemptRepository
from app.repositories.exam import ExamRepository
from app.repositories.grade import GradeRepository
from app.repositories.omr import OMRScanRepository, OMRTemplateRepository
from app.repositories.skill import SkillRepository
from app.schemas.exam import ExamCreate, ExamUpdate
from app.schemas.omr import OMRTemplateCreate
from app.services.answer_key import AnswerKeyService
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

    def create_exam(self, exam_in: ExamCreate, teacher_id: UUID) -> Exam:
        if exam_in.questions and exam_in.correct_answers:
            raise ValueError(
                "Provide either Workflow A questions or Workflow B correct_answers, not both."
            )

        if exam_in.questions:
            exam_in.total_questions = len(exam_in.questions)

        # 1. If omr_template_id not provided, create an OMRTemplate automatically
        omr_template_id = exam_in.omr_template_id
        if not omr_template_id and exam_in.correct_answers:
            layout_ver = exam_in.layout_version or (
                "v1_std_50q" if exam_in.total_questions > 20 else "v1_std_20q"
            )
            template_in = OMRTemplateCreate(
                layout_version=layout_ver,
                total_questions=exam_in.total_questions,
                options_per_question=5,
                correct_answers=exam_in.correct_answers,
            )
            tmpl = self.template_repo.create(template_in)
            omr_template_id = tmpl.id

        exam_in.omr_template_id = omr_template_id
        exam = self.exam_repo.create(exam_in, teacher_id=teacher_id)

        # 2. Link OMRTemplate back to exam
        if omr_template_id:
            tmpl = self.template_repo.get_by_id(omr_template_id)
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

        self.db.refresh(exam)
        return exam

    def publish_exam(self, exam_id: UUID) -> Exam:
        exam = self._require_exam(exam_id)
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

    def return_exam_to_draft(self, exam_id: UUID) -> Exam:
        exam = self._require_exam(exam_id)
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

    def archive_exam(self, exam_id: UUID) -> Exam:
        exam = self._require_exam(exam_id)
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

    def _require_exam(self, exam_id: UUID) -> Exam:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")
        return exam

    def get_exam(self, exam_id: UUID) -> Optional[Exam]:
        return self.exam_repo.get_by_id(exam_id)

    def list_exams(
        self, teacher_id: Optional[UUID] = None, class_id: Optional[str] = None
    ) -> List[Exam]:
        return self.exam_repo.get_all(teacher_id=teacher_id, class_id=class_id)

    def update_exam(self, exam_id: UUID, update_in: ExamUpdate) -> Optional[Exam]:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            return None
        if exam.status == ExamStatus.ARCHIVED.value:
            raise ValueError(f"Exam {exam_id} is archived and cannot be edited.")
        return self.exam_repo.update(exam_id, update_in)

    def soft_delete_exam(self, exam_id: UUID) -> bool:
        """
        Soft deletes an exam (sets is_active=False, deleted_at=now()).
        Preserves historical Attempt, AttemptAnswer and Grade records!
        """
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            return False
        self.archive_exam(exam.id)
        return True

    def soft_delete_template(self, template_id: UUID) -> bool:
        """
        Soft deletes an OMR template (sets is_active=False, deleted_at=now()).
        Preserves OMR scans and historical grades.
        """
        tmpl = self.template_repo.get_by_id(template_id)
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

    def get_exam_statistics(self, exam_id: UUID) -> Dict[str, Any]:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
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

    def export_exam_pdf(self, exam_id: UUID) -> bytes:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")

        teacher = self.db.query(User).filter(User.id == exam.teacher_id).first()
        teacher_name = teacher.email if teacher else "Professor"

        stats = self.get_exam_statistics(exam_id)
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

    def export_exam_xlsx(self, exam_id: UUID) -> bytes:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")

        teacher = self.db.query(User).filter(User.id == exam.teacher_id).first()
        teacher_name = teacher.email if teacher else "Professor"

        stats = self.get_exam_statistics(exam_id)
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
