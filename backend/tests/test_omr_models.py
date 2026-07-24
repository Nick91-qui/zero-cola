from decimal import Decimal
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
        correct_answers={"1": "A", "2": "B"},
    )
    test_db_session.add(template)
    test_db_session.commit()

    assert template.id is not None
    assert template.layout_version == "v1_std_20q"
    assert template.total_questions == 20
    assert template.options_per_question == 5
    assert template.correct_answers == {"1": "A", "2": "B"}


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
