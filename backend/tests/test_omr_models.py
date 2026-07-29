from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.models.enums import GradeSourceType, OMRScanStatus, UserRole
from app.models.grade import Grade
from app.models.omr import OMRScan, OMRTemplate
from app.models.user import User


def test_omr_template_creation(test_db_session):
    template = OMRTemplate(
        layout_version="v1_std_20q",
        total_questions=20,
        options_per_question=5,
    )
    test_db_session.add(template)
    test_db_session.commit()

    assert template.id is not None
    assert template.layout_version == "v1_std_20q"
    assert template.total_questions == 20
    assert template.options_per_question == 5
    assert "created_by" in OMRTemplate.__table__.c
    assert "correct_answers" not in OMRTemplate.__table__.c
    assert not hasattr(template, "correct_answers")


def test_step4_migration_drops_omr_template_correct_answers() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "c3d4e5f6a7b8_drop_omr_template_correct_answers.py"
    )
    source = migration_path.read_text()

    assert "revision: str = \"c3d4e5f6a7b8\"" in source
    assert "down_revision: Union[str, None] = \"b2c3d4e5f6a7\"" in source
    assert "op.drop_column(\"omr_templates\", \"correct_answers\")" in source
    assert 'sa.Column("correct_answers", sa.JSON(), nullable=True)' in source


def test_omr_scan_creation_and_relations(test_db_session):
    student = User(email="student@cola-zero.edu", password_hash="fake_hash", role=UserRole.STUDENT)
    test_db_session.add(student)

    template = OMRTemplate(layout_version="v1_std_20q", total_questions=20)
    test_db_session.add(template)
    test_db_session.commit()

    scan = OMRScan(
        omr_template_id=template.id,
        student_code="12345",
        student_id=student.id,
        status=OMRScanStatus.SUCCESS,
        image_url="http://storage.local/scans/scan1.png",
        detected_answers={"1": "A", "2": "B"},
        raw_confidence={"1": 0.95, "2": 0.88},
        score=Decimal("10.00"),
    )
    test_db_session.add(scan)
    test_db_session.commit()

    assert scan.id is not None
    assert scan.omr_template.layout_version == "v1_std_20q"
    assert scan.student.email == "student@cola-zero.edu"
    assert scan.status == OMRScanStatus.SUCCESS
    assert scan.score == Decimal("10.00")


def test_grade_creation_and_relations(test_db_session):
    student = User(email="student2@cola-zero.edu", password_hash="fake_hash", role=UserRole.STUDENT)
    teacher = User(email="teacher@cola-zero.edu", password_hash="fake_hash", role=UserRole.TEACHER)
    test_db_session.add_all([student, teacher])
    test_db_session.commit()

    grade = Grade(
        student_id=student.id,
        source_type=GradeSourceType.OMR,
        source_id=uuid4(),
        score=Decimal("8.50"),
        teacher_id=teacher.id,
    )
    test_db_session.add(grade)
    test_db_session.commit()

    assert grade.id is not None
    assert grade.student.email == "student2@cola-zero.edu"
    assert grade.teacher.email == "teacher@cola-zero.edu"
    assert grade.score == Decimal("8.50")
    assert grade.source_type == GradeSourceType.OMR
