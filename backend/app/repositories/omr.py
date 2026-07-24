from uuid import UUID

from sqlalchemy.orm import Session

from app.models.omr import OMRScan, OMRTemplate
from app.schemas.omr import OMRTemplateCreate


class OMRTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, template_in: OMRTemplateCreate) -> OMRTemplate:
        db_template = OMRTemplate(
            exam_id=template_in.exam_id,
            layout_version=template_in.layout_version,
            total_questions=template_in.total_questions,
            options_per_question=template_in.options_per_question,
            correct_answers=template_in.correct_answers,
        )
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def get_by_id(self, template_id: str | UUID) -> OMRTemplate | None:
        if isinstance(template_id, str):
            template_id = UUID(template_id)
        return self.db.query(OMRTemplate).filter(OMRTemplate.id == template_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[OMRTemplate]:
        return self.db.query(OMRTemplate).offset(skip).limit(limit).all()


class OMRScanRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, omr_template_id: UUID, image_url: str) -> OMRScan:
        db_scan = OMRScan(
            omr_template_id=omr_template_id,
            image_url=image_url,
        )
        self.db.add(db_scan)
        self.db.commit()
        self.db.refresh(db_scan)
        return db_scan

    def get_by_id(self, scan_id: str | UUID) -> OMRScan | None:
        if isinstance(scan_id, str):
            scan_id = UUID(scan_id)
        return self.db.query(OMRScan).filter(OMRScan.id == scan_id).first()

    def update(self, scan_id: str | UUID, **kwargs) -> OMRScan | None:
        if isinstance(scan_id, str):
            scan_id = UUID(scan_id)
        scan = self.get_by_id(scan_id)
        if scan:
            for key, value in kwargs.items():
                if hasattr(scan, key):
                    setattr(scan, key, value)
            self.db.commit()
            self.db.refresh(scan)
        return scan
