from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.omr import OMRScan, OMRTemplate
from app.schemas.omr import OMRTemplateCreate


class OMRTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        template_in: OMRTemplateCreate,
        created_by: UUID | None = None,
    ) -> OMRTemplate:
        db_template = OMRTemplate(
            exam_id=template_in.exam_id,
            created_by=created_by,
            layout_version=template_in.layout_version,
            total_questions=template_in.total_questions,
            options_per_question=template_in.options_per_question,
        )
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template

    def get_by_id(
        self,
        template_id: str | UUID,
        owner_id: UUID | None = None,
    ) -> OMRTemplate | None:
        if isinstance(template_id, str):
            template_id = UUID(template_id)
        query = self.db.query(OMRTemplate).filter(OMRTemplate.id == template_id)
        if owner_id is not None:
            query = query.outerjoin(Exam, Exam.id == OMRTemplate.exam_id).filter(
                or_(
                    OMRTemplate.created_by == owner_id,
                    and_(
                        OMRTemplate.created_by.is_(None),
                        Exam.teacher_id == owner_id,
                    ),
                )
            )
        return query.first()

    def get_all(
        self,
        owner_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OMRTemplate]:
        query = self.db.query(OMRTemplate)
        if owner_id is not None:
            query = query.outerjoin(Exam, Exam.id == OMRTemplate.exam_id).filter(
                or_(
                    OMRTemplate.created_by == owner_id,
                    and_(
                        OMRTemplate.created_by.is_(None),
                        Exam.teacher_id == owner_id,
                    ),
                )
            )
        return query.offset(skip).limit(limit).all()


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
