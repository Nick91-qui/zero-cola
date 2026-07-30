from pathlib import Path

from app.db.models import BaseModel
from app.models.attempt import Attempt
from app.models.audit_log import AuditLog
from app.models.class_ import Class, ClassStudent
from app.models.consent import Consent
from app.models.enums import AttemptStatus, ExamStatus
from app.models.exam import Exam
from app.models.security_event import SecurityEvent
from app.models.user import User


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


def test_step9_models_define_classes_monitoring_and_lgpd_tables() -> None:
    assert "anonymized_at" in User.__table__.c

    class_table = Class.__table__
    assert class_table.name == "classes"
    assert "teacher_id" in class_table.c
    assert any(
        constraint.name == "uq_classes_teacher_name" for constraint in class_table.constraints
    )

    class_student_table = ClassStudent.__table__
    assert class_student_table.name == "class_students"
    assert "student_id" in class_student_table.c
    assert any(
        constraint.name == "uq_class_students_class_student"
        for constraint in class_student_table.constraints
    )

    audit_log_table = AuditLog.__table__
    assert audit_log_table.name == "audit_logs"
    assert "metadata" in audit_log_table.c

    security_event_table = SecurityEvent.__table__
    assert security_event_table.name == "security_events"
    assert "attempt_id" in security_event_table.c

    consent_table = Consent.__table__
    assert consent_table.name == "consents"
    assert any(
        constraint.name == "uq_consents_user_consent_type"
        for constraint in consent_table.constraints
    )


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


def test_step9_migration_source_declares_classes_monitoring_and_lgpd_support() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "f7a8b9c0d1e2_add_step9_classes_audit_security_privacy.py"
    )
    source = migration_path.read_text()

    assert "Revision ID: f7a8b9c0d1e2" in source
    assert "Revises: e6f7a8b9c0d1" in source
    assert '"anonymized_at"' in source
    assert '"classes"' in source
    assert '"class_students"' in source
    assert '"audit_logs"' in source
    assert '"security_events"' in source
    assert '"consents"' in source
