from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import GradeSourceType
from app.models.grade import Grade


class GradeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update(
        self,
        student_id: UUID,
        source_type: GradeSourceType,
        source_id: UUID,
        score: Decimal,
        teacher_id: UUID,
    ) -> Grade:
        # Check if grade already exists for this source
        db_grade = (
            self.db.query(Grade)
            .filter(Grade.source_type == source_type, Grade.source_id == source_id)
            .first()
        )

        if db_grade:
            db_grade.score = score
            db_grade.teacher_id = teacher_id
            db_grade.student_id = student_id
        else:
            db_grade = Grade(
                student_id=student_id,
                source_type=source_type,
                source_id=source_id,
                score=score,
                teacher_id=teacher_id,
            )
            self.db.add(db_grade)

        self.db.commit()
        self.db.refresh(db_grade)
        return db_grade

    def get_by_id(self, grade_id: str | UUID) -> Grade | None:
        if isinstance(grade_id, str):
            grade_id = UUID(grade_id)
        return self.db.query(Grade).filter(Grade.id == grade_id).first()

    def get_by_source(self, source_type: GradeSourceType, source_id: UUID) -> Grade | None:
        return (
            self.db.query(Grade)
            .filter(Grade.source_type == source_type, Grade.source_id == source_id)
            .first()
        )
