import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.enums import GradeSourceType, OMRScanStatus, UserRole
from app.models.grade import Grade
from app.models.omr import OMRScan, OMRTemplate
from app.models.user import User
from app.repositories.grade import GradeRepository
from app.repositories.omr import OMRScanRepository, OMRTemplateRepository
from app.repositories.user import UserRepository
from app.schemas.omr import OMRScanUpdate, OMRTemplateCreate
from app.services.omr_engine import OMREngine
from app.services.omr_pdf import generate_omr_pdf
from app.services.omr_sheet_image import render_sheet_png


class OMRService:
    def __init__(self, db: Session, upload_dir: str = "uploads/scans"):
        self.db = db
        self.upload_dir = upload_dir
        self.template_repo = OMRTemplateRepository(db)
        self.scan_repo = OMRScanRepository(db)
        self.grade_repo = GradeRepository(db)
        self.user_repo = UserRepository(db)

    def create_template(self, template_in: OMRTemplateCreate) -> OMRTemplate:
        return self.template_repo.create(template_in)

    def list_templates(self) -> list[OMRTemplate]:
        return self.template_repo.get_all()

    def get_template(self, template_id: UUID) -> Optional[OMRTemplate]:
        return self.template_repo.get_by_id(template_id)

    def get_template_pdf(self, template_id: UUID, student_code: Optional[str] = None) -> bytes:
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"OMR Template with ID {template_id} not found.")
        return generate_omr_pdf(template.layout_version, student_code)

    def get_template_preview_png(
        self,
        template_id: UUID,
        student_code: Optional[str] = None,
        answers: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """Renders a PNG preview in the same coordinate space used by the OMR engine."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"OMR Template with ID {template_id} not found.")
        return render_sheet_png(
            template.layout_version,
            student_code=student_code,
            answers=answers or {},
        )

    def _save_uploaded_file(self, file_bytes: bytes, filename: str) -> str:
        """Saves the uploaded file to disk and returns the relative image url."""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)

        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            raise ValueError("Only JPG, JPEG, and PNG images are allowed.")

        unique_filename = f"{uuid4()}{ext}"
        filepath = os.path.join(self.upload_dir, unique_filename)

        with open(filepath, "wb") as f:
            f.write(file_bytes)

        return filepath

    def process_scan_upload(self, template_id: UUID, file_bytes: bytes, filename: str) -> OMRScan:
        """
        Saves the OMR image, creates an OMRScan record, and processes the image
        to detect student code and answers.
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"OMR Template with ID {template_id} not found.")

        # 1. Save file
        image_url = self._save_uploaded_file(file_bytes, filename)

        # 2. Create OMRScan with status processing
        scan = self.scan_repo.create(omr_template_id=template_id, image_url=image_url)

        # 3. Perform OMR detection
        try:
            detected = OMREngine.process_image(file_bytes, template.layout_version)

            # Resolve student_id from student_code if detected
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

            # Grade scan
            score = self._calculate_score(template, detected.get("detected_answers", {}))

            # Check for anomalies (e.g. MULTIPLE answers or missing code)
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
            # Mark scan as failed
            self.scan_repo.update(
                scan.id,
                status=OMRScanStatus.FAILED,
                error_message=str(e),
                processed_at=datetime.now(),
            )

        # Refresh and return
        self.db.refresh(scan)
        return scan

    def _calculate_score(self, template: OMRTemplate, detected_answers: Dict[str, str]) -> Decimal:
        """Calculates the score based on template's correct answers."""
        if not template.correct_answers or not detected_answers:
            return Decimal("0.00")

        correct_count = 0
        total_questions = template.total_questions

        for q_str, correct_ans in template.correct_answers.items():
            if detected_answers.get(q_str) == correct_ans:
                correct_count += 1

        # Scaled to a max score of 10.0
        score = (Decimal(correct_count) / Decimal(total_questions)) * Decimal("10.00")
        return score.quantize(Decimal("0.01"))

    def update_scan_manual(self, scan_id: UUID, update_in: OMRScanUpdate) -> OMRScan:
        """Allows manual adjustment of student code and answers by the teacher."""
        scan = self.scan_repo.get_by_id(scan_id)
        if not scan:
            raise ValueError(f"OMR Scan with ID {scan_id} not found.")

        template = self.get_template(scan.omr_template_id)
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

    def confirm_scan(self, scan_id: UUID, teacher_id: UUID) -> Grade:
        """Confirms OMR correction and publishes the grade to the unified grades table."""
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

        # 2. Record to unified grades table
        grade = self.grade_repo.create_or_update(
            student_id=scan.student_id,
            source_type=GradeSourceType.OMR,
            source_id=scan.id,
            score=scan.score,
            teacher_id=teacher_id,
        )
        return grade
