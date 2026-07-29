from app.db.models import BaseModel
from app.models.enums import ExamStatus
from app.models.exam import Exam


class ExampleModel(BaseModel):
    __tablename__ = "example_models"


def test_base_model_uses_uuid_primary_key() -> None:
    table = ExampleModel.__table__

    assert table.c.id.primary_key is True
    assert table.c.id.type.as_uuid is True


def test_base_model_includes_audit_timestamps() -> None:
    table = ExampleModel.__table__

    assert "created_at" in table.c
    assert "updated_at" in table.c
    assert str(table.c.created_at.server_default.arg) == "now()"
    assert str(table.c.updated_at.server_default.arg) == "now()"


def test_exam_model_has_lifecycle_status() -> None:
    table = Exam.__table__

    assert "status" in table.c
    assert table.c.status.nullable is False
    assert str(table.c.status.server_default.arg) == ExamStatus.DRAFT.value
    assert any(constraint.name == "ck_exams_status_valid" for constraint in table.constraints)
