import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import GradeSourceType, OMRScanStatus, UserRole
from app.models.exam import Exam
from app.models.grade import Grade
from app.models.omr import OMRScan, OMRTemplate
from app.models.user import User
from app.repositories.grade import GradeRepository
from app.repositories.omr import OMRScanRepository, OMRTemplateRepository
from app.repositories.user import UserRepository
from app.schemas.exam import ExamCreate
from app.schemas.omr import OMRScanUpdate, OMRTemplateCreate
from app.services.answer_key import AnswerKeyService
from app.services.exam import ExamService
from app.services.omr_engine import OMREngine
from app.services.omr_pdf import generate_omr_pdf
from app.services.omr_sheet_image import render_sheet_png
from app.services.omr_storage import OMRScanStorage


class OMRService:
    def __init__(self, db: Session, upload_dir: str = "uploads/scans"):
        self.db = db
        self.upload_dir = upload_dir
        self.scan_storage = OMRScanStorage(upload_dir)
        self.template_repo = OMRTemplateRepository(db)
        self.scan_repo = OMRScanRepository(db)
        self.grade_repo = GradeRepository(db)
        self.user_repo = UserRepository(db)
        self.answer_key_service = AnswerKeyService(db)

    def create_template(
        self,
        template_in: OMRTemplateCreate,
        teacher_id: UUID | None = None,
    ) -> OMRTemplate:
        if template_in.correct_answers:
            if teacher_id is None:
                raise ValueError(
                    "teacher_id is required when creating a template with answer keys."
                )

            exam_service = ExamService(self.db)
            exam = exam_service.create_exam(
                ExamCreate(
                    title=f"Avaliação OMR {template_in.layout_version}",
                    description=None,
                    class_id=None,
                    omr_template_id=None,
                    total_questions=template_in.total_questions,
                    max_score=Decimal("10.00"),
                    correct_answers=template_in.correct_answers,
                    layout_version=template_in.layout_version,
                ),
                teacher_id=teacher_id,
                owner_id=teacher_id,
            )
            return self.template_repo.get_by_id(exam.omr_template_id, owner_id=teacher_id)

        return self.template_repo.create(template_in, created_by=teacher_id)

    def list_templates(self, owner_id: UUID | None = None) -> list[OMRTemplate]:
        return self.template_repo.get_all(owner_id=owner_id)

    def get_template(
        self,
        template_id: UUID,
        owner_id: UUID | None = None,
    ) -> Optional[OMRTemplate]:
        return self.template_repo.get_by_id(template_id, owner_id=owner_id)

    def get_template_pdf(
        self,
        template_id: UUID,
        student_code: Optional[str] = None,
        owner_id: UUID | None = None,
    ) -> bytes:
        template = self.get_template(template_id, owner_id=owner_id)
        if not template:
            raise ValueError(f"OMR Template with ID {template_id} not found.")
        return generate_omr_pdf(
            template.layout_version,
            student_code,
            exam_title=template.title,
        )

    def get_template_preview_png(
        self,
        template_id: UUID,
        student_code: Optional[str] = None,
        answers: Optional[Dict[str, str]] = None,
        owner_id: UUID | None = None,
    ) -> bytes:
        """Renders a PNG preview in the same coordinate space used by the OMR engine."""
        template = self.get_template(template_id, owner_id=owner_id)
        if not template:
            raise ValueError(f"OMR Template with ID {template_id} not found.")
        return render_sheet_png(
            template.layout_version,
            student_code=student_code,
            exam_title=template.title,
            answers=answers or {},
        )

    def get_scan(self, scan_id: UUID, owner_id: UUID | None = None) -> Optional[OMRScan]:
        scan = self.scan_repo.get_by_id(scan_id)
        if not scan:
            return None
        if owner_id is None:
            return scan
        template = self.get_template(scan.omr_template_id, owner_id=owner_id)
        if not template:
            return None
        return scan

    def _save_uploaded_file(self, file_bytes: bytes, filename: str) -> str:
        """Saves the uploaded file through the configured storage backend."""
        return self.scan_storage.save(file_bytes, filename)

    def _process_scan_from_image(
        self,
        template: OMRTemplate,
        file_bytes: bytes,
        filename: str,
    ) -> OMRScan:
        """Processes one image page and persists the resulting scan."""
        image_url = self._save_uploaded_file(file_bytes, filename)

        scan = self.scan_repo.create(omr_template_id=template.id, image_url=image_url)

        try:
            detected = OMREngine.process_image(file_bytes, template.layout_version)

            student_code = detected.get("student_code")
            student_id = None
            if student_code:
                student = (
                    self.db.query(User)
                    .filter(
                        User.student_code == student_code,
                        User.role == UserRole.STUDENT,
                        User.is_active,
                    )
                    .first()
                )
                if student:
                    student_id = student.id

            score = self._calculate_score(template, detected.get("detected_answers", {}))

            status = OMRScanStatus.SUCCESS
            error_msg = None

            if "MULTIPLE" in detected.get("detected_answers", {}).values():
                status = OMRScanStatus.REVIEW_NEEDED
                error_msg = "Double markings detected on one or more questions."
            elif not student_id:
                status = OMRScanStatus.REVIEW_NEEDED
                error_msg = f"Could not find student with code: {student_code}"

            self.scan_repo.update(
                scan.id,
                student_code=student_code,
                student_id=student_id,
                status=status,
                detected_answers=detected.get("detected_answers"),
                raw_confidence=detected.get("raw_confidence"),
                score=score,
                error_message=error_msg,
                processed_at=datetime.now(),
            )
        except Exception as e:
            self.scan_repo.update(
                scan.id,
                status=OMRScanStatus.FAILED,
                error_message=str(e),
                processed_at=datetime.now(),
            )

        self.db.refresh(scan)
        return scan

    def _extract_pdf_pages(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> list[tuple[bytes, str]]:
        """Converts a PDF into PNG page images using the system's pdftoppm utility."""
        if shutil.which("pdftoppm") is None:
            raise ValueError("PDF batch processing is unavailable in this environment.")

        pages: list[tuple[bytes, str]] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pdf_path = tmp_path / "upload.pdf"
            output_prefix = tmp_path / "page"
            pdf_path.write_bytes(file_bytes)

            result = subprocess.run(
                ["pdftoppm", "-png", str(pdf_path), str(output_prefix)],
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="ignore").strip()
                raise ValueError(
                    "Failed to convert PDF pages to images."
                    + (f" pdftoppm error: {stderr}" if stderr else "")
                )

            page_files = sorted(
                tmp_path.glob("page-*.png"),
                key=lambda path: int(path.stem.split("-")[-1]),
            )
            if not page_files:
                raise ValueError("The uploaded PDF did not contain any pages.")

            base_name = Path(filename).stem or "scan"
            for index, page_file in enumerate(page_files, start=1):
                pages.append((page_file.read_bytes(), f"{base_name}_page_{index}.png"))

        return pages

    def process_scan_upload(
        self,
        template_id: UUID,
        file_bytes: bytes,
        filename: str,
        owner_id: UUID | None = None,
    ) -> OMRScan:
        """
        Saves the OMR image, creates an OMRScan record, and processes the image
        to detect student code and answers.
        """
        template = self.get_template(template_id, owner_id=owner_id)
        if not template:
            raise ValueError(f"OMR Template with ID {template_id} not found.")

        return self._process_scan_from_image(template, file_bytes, filename)

    def process_scan_upload_batch(
        self,
        template_id: UUID,
        file_bytes: bytes,
        filename: str,
        owner_id: UUID | None = None,
    ) -> list[OMRScan]:
        """Processes a PDF batch or a single image into one scan per page."""
        template = self.get_template(template_id, owner_id=owner_id)
        if not template:
            raise ValueError(f"OMR Template with ID {template_id} not found.")

        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            pages = self._extract_pdf_pages(file_bytes, filename)
        else:
            pages = [(file_bytes, filename)]

        scans: list[OMRScan] = []
        for page_bytes, page_filename in pages:
            scans.append(self._process_scan_from_image(template, page_bytes, page_filename))
        return scans

    def _calculate_score(self, template: OMRTemplate, detected_answers: Dict[str, str]) -> Decimal:
        """Calculates the score based on AnswerKeyItems."""
        if not detected_answers:
            return Decimal("0.00")

        answer_key_items = self._require_answer_key_items(template)
        if not answer_key_items:
            return Decimal("0.00")

        correct_count = 0
        total_questions = template.total_questions

        for item in answer_key_items:
            q_str = str(item.item_number)
            q_key = f"q{item.item_number}"
            if (
                detected_answers.get(q_str) == item.correct_answer
                or detected_answers.get(q_key) == item.correct_answer
            ):
                correct_count += 1

        # Scaled to a max score of 10.0
        score = (Decimal(correct_count) / Decimal(total_questions)) * Decimal("10.00")
        return score.quantize(Decimal("0.01"))

    def update_scan_manual(
        self,
        scan_id: UUID,
        update_in: OMRScanUpdate,
        owner_id: UUID | None = None,
    ) -> OMRScan:
        """Allows manual adjustment of student code and answers by the teacher."""
        scan = self.scan_repo.get_by_id(scan_id)
        if not scan:
            raise ValueError(f"OMR Scan with ID {scan_id} not found.")

        template = self.get_template(scan.omr_template_id, owner_id=owner_id)
        if not template:
            raise ValueError("OMR Template for this scan was not found.")

        update_data = update_in.model_dump(exclude_unset=True)

        # If student code updated, re-resolve student_id
        if "student_code" in update_data and update_data["student_code"] != scan.student_code:
            new_code = update_data["student_code"]
            student_id = None
            if new_code:
                student = (
                    self.db.query(User)
                    .filter(
                        User.student_code == new_code,
                        User.role == UserRole.STUDENT,
                        User.is_active,
                    )
                    .first()
                )
                if student:
                    student_id = student.id
            update_data["student_id"] = student_id

        # If detected answers or student code updated, recalculate score
        answers = update_data.get("detected_answers", scan.detected_answers)
        if answers:
            update_data["score"] = self._calculate_score(template, answers)

        updated_scan = self.scan_repo.update(scan_id, **update_data)
        return updated_scan

    def confirm_scan(
        self,
        scan_id: UUID,
        teacher_id: UUID,
        owner_id: UUID | None = None,
    ) -> Grade:
        """Confirms OMR correction, creates Attempt rows, and publishes the grade."""
        from app.repositories.attempt import AttemptRepository

        scan = self.scan_repo.get_by_id(scan_id)
        if not scan:
            raise ValueError(f"OMR Scan with ID {scan_id} not found.")

        if not scan.student_id:
            raise ValueError(
                "Cannot confirm OMR scan because no student is associated with it. "
                "Please resolve student ID first."
            )

        if scan.score is None:
            raise ValueError("Cannot confirm OMR scan because it does not have a calculated score.")

        # 1. Update scan status to SUCCESS
        self.scan_repo.update(scan.id, status=OMRScanStatus.SUCCESS, error_message=None)

        # 2. Resolve the linked Exam and canonical AnswerKey.
        template = self.get_template(scan.omr_template_id, owner_id=owner_id)
        if not template:
            raise ValueError(f"OMR Template with ID {scan.omr_template_id} not found.")
        if not template.exam_id:
            raise ValueError("Cannot confirm OMR scan because it is not linked to an Exam.")

        exam = self.db.query(Exam).filter(Exam.id == template.exam_id).first()
        if not exam:
            raise ValueError("Cannot confirm OMR scan because the linked Exam was not found.")

        answer_key_items = self._require_answer_key_items(template)
        answer_key_item_map = {item.item_number: item for item in answer_key_items}

        # 3. Calculate score breakdown and prepare AttemptAnswers.
        correct_cnt = 0
        answers_data = []
        tot_q = template.total_questions if template else 20
        for i in range(1, tot_q + 1):
            answer_key_item = answer_key_item_map.get(i)
            if not answer_key_item:
                continue

            q_str_i = str(i)
            q_key_i = f"q{i}"
            selected_opt = None
            if scan.detected_answers:
                selected_opt = (
                    scan.detected_answers.get(q_str_i)
                    or scan.detected_answers.get(q_key_i)
                )

            correct_opt = answer_key_item.correct_answer
            is_corr = bool(selected_opt and correct_opt and selected_opt == correct_opt)
            if is_corr:
                correct_cnt += 1

            answers_data.append(
                {
                    "attempt_id": None,
                    "question_number": i,
                    "answer_key_item_id": answer_key_item.id,
                    "question_id": answer_key_item.question_id,
                    "selected_option": selected_opt,
                    "correct_option": correct_opt,
                    "is_correct": is_corr,
                    "answered_at": datetime.now(timezone.utc),
                }
            )

        incorr_cnt = tot_q - correct_cnt
        accuracy_pct = Decimal((correct_cnt / tot_q) * 100) if tot_q > 0 else Decimal("0.00")
        raw_score = Decimal(correct_cnt)
        final_score = (
            (Decimal(correct_cnt) / Decimal(tot_q)) * exam.max_score
            if tot_q > 0
            else Decimal("0.00")
        )

        # 4. Create or update Attempt
        attempt_repo = AttemptRepository(self.db)
        existing_attempt = attempt_repo.get_by_omr_scan_id(scan.id)
        if not existing_attempt:
            attempt = attempt_repo.create_attempt(
                exam_id=exam.id,
                answer_key_id=exam.answer_key.id,
                student_id=scan.student_id,
                student_code=scan.student_code,
                omr_scan_id=scan.id,
                total_questions=tot_q,
                correct_answers=correct_cnt,
                incorrect_answers=incorr_cnt,
                accuracy_percentage=accuracy_pct.quantize(Decimal("0.01")),
                raw_score=raw_score.quantize(Decimal("0.01")),
                final_score=final_score.quantize(Decimal("0.01")),
                source="OMR",
                status="graded",
            )
            for a_item in answers_data:
                a_item["attempt_id"] = attempt.id
            attempt_repo.create_answers_bulk(answers_data)

        # 5. Update scan.score to final_score
        self.scan_repo.update(scan.id, score=final_score.quantize(Decimal("0.01")))

        # 6. Record to unified grades table
        grade = self.grade_repo.create_or_update(
            student_id=scan.student_id,
            source_type=GradeSourceType.OMR,
            source_id=scan.id,
            score=final_score.quantize(Decimal("0.01")),
            teacher_id=teacher_id,
        )
        return grade

    def delete_template(self, template_id: UUID, owner_id: UUID | None = None) -> bool:
        template = self.template_repo.get_by_id(template_id, owner_id=owner_id)
        if not template:
            return False
        template.is_active = False
        template.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def _require_answer_key_items(self, template: OMRTemplate):
        if not template.exam_id:
            raise ValueError("Cannot grade OMR template without a linked Exam.")
        return self.answer_key_service.get_items_for_exam(template.exam_id)
