from decimal import Decimal
from app.models.enums import UserRole
from app.models.omr import OMRTemplate
from app.models.user import User
from app.schemas.exam import ExamCreate
from app.services.exam import ExamService


def test_create_exam_with_auto_template(test_db_session):
    teacher = User(
        email="teacher_exam@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam_in = ExamCreate(
        title="Prova de Matemática",
        description="Avaliação P1",
        class_id="301",
        total_questions=20,
        max_score=Decimal("10.00"),
        correct_answers={"1": "A", "2": "B", "3": "C"},
    )
    exam = service.create_exam(exam_in, teacher_id=teacher.id)

    assert exam.id is not None
    assert exam.title == "Prova de Matemática"
    assert exam.teacher_id == teacher.id
    assert exam.omr_template_id is not None
    assert exam.total_questions == 20
    assert len(exam.questions) == 3


def test_soft_delete_exam_and_template(test_db_session):
    teacher = User(
        email="teacher_del@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam_in = ExamCreate(
        title="Prova Deletar",
        total_questions=20,
        correct_answers={"1": "A"},
    )
    exam = service.create_exam(exam_in, teacher_id=teacher.id)
    tmpl_id = exam.omr_template_id

    success = service.soft_delete_exam(exam.id)
    assert success is True

    deleted_exam = service.get_exam(exam.id)
    assert deleted_exam is None  # default get_exam excludes inactive

    tmpl = test_db_session.query(OMRTemplate).filter(OMRTemplate.id == tmpl_id).first()
    assert tmpl is not None
    assert tmpl.is_active is False
