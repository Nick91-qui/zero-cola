from pathlib import Path

from app.db.models import BaseModel
from app.models.attempt import Attempt
from app.models.enums import AttemptStatus, ExamStatus
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


def test_exam_model_has_online_attempt_fields() -> None:
    table = Exam.__table__

    assert "total_time_seconds" in table.c
    assert "max_attempts" in table.c
    assert "randomization_enabled" in table.c
    assert table.c.total_time_seconds.nullable is True
    assert table.c.max_attempts.nullable is False
    assert table.c.randomization_enabled.nullable is False
    assert str(table.c.max_attempts.server_default.arg) == "1"
    assert str(table.c.randomization_enabled.server_default.arg) == "false"


def test_attempt_model_has_online_lifecycle_status() -> None:
    table = Attempt.__table__

    assert "status" in table.c
    assert table.c.status.nullable is False
    assert str(table.c.status.server_default.arg) == AttemptStatus.NOT_STARTED.value
    assert any(constraint.name == "ck_attempts_status_valid" for constraint in table.constraints)


def test_step8_migration_source_declares_online_fields():
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "d1e2f3a4b5c6_add_online_attempt_engine_fields.py"
    )
    source = migration_path.read_text()

    assert "Revision ID: d1e2f3a4b5c6" in source
    assert "Revises: e5f6a7b8c9d0" in source
    assert "total_time_seconds" in source
    assert "max_attempts" in source
    assert "randomization_enabled" in source
    assert "ck_attempts_status_valid" in source
