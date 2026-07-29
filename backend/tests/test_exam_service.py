from decimal import Decimal

from app.models.answer_key import AnswerKey, AnswerKeyItem
from app.models.enums import UserRole
from app.models.omr import OMRTemplate
from app.models.question import Question
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamQuestionCreate, QuestionCreate
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
    assert len(exam.questions) == 0
    assert exam.answer_key is not None
    assert len(exam.answer_key.items) == 3


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


def test_exam_statistics_use_answer_key_items(test_db_session):
    teacher = User(
        email="teacher_stats@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Estatísticas por AnswerKey",
            total_questions=20,
            correct_answers={"1": "A", "2": "B"},
        ),
        teacher_id=teacher.id,
    )

    answer_key_item = (
        test_db_session.query(AnswerKeyItem)
        .join(AnswerKey)
        .filter(AnswerKey.exam_id == exam.id, AnswerKeyItem.item_number == 1)
        .first()
    )
    assert answer_key_item is not None
    answer_key_item.correct_answer = "D"
    test_db_session.commit()

    stats = service.get_exam_statistics(exam.id)

    assert len(stats["question_statistics"]) == 20
    assert stats["question_statistics"][0]["correct_option"] == "D"


def test_create_exam_with_question_bank_creates_exam_questions(test_db_session):
    teacher = User(
        email="teacher_bank@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Banco de questões",
            total_questions=2,
            questions=[
                ExamQuestionCreate(
                    display_order=2,
                    question=QuestionCreate(
                        statement="Questão 2",
                        correct_answer="B",
                    ),
                ),
                ExamQuestionCreate(
                    display_order=1,
                    question=QuestionCreate(
                        statement="Questão 1",
                        correct_answer="A",
                    ),
                ),
            ],
        ),
        teacher_id=teacher.id,
    )

    test_db_session.refresh(exam)

    assert exam.answer_key is not None
    assert len(exam.exam_questions) == 2
    assert [eq.display_order for eq in exam.exam_questions] == [1, 2]
    assert [q.statement for q in exam.questions] == ["Questão 1", "Questão 2"]
    assert [item.correct_answer for item in exam.answer_key.items] == ["A", "B"]


def test_create_exam_can_reuse_existing_question(test_db_session):
    teacher = User(
        email="teacher_reuse@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    reusable_question = Question(
        statement="Questão reutilizável",
        type="multiple_choice",
        options={"A": "A", "B": "B"},
        correct_answer="A",
        created_by=teacher.id,
    )
    test_db_session.add(reusable_question)
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam1 = service.create_exam(
        ExamCreate(
            title="Prova 1",
            total_questions=1,
            questions=[
                ExamQuestionCreate(display_order=1, question_id=reusable_question.id),
            ],
        ),
        teacher_id=teacher.id,
    )
    exam2 = service.create_exam(
        ExamCreate(
            title="Prova 2",
            total_questions=1,
            questions=[
                ExamQuestionCreate(display_order=1, question_id=reusable_question.id),
            ],
        ),
        teacher_id=teacher.id,
    )

    test_db_session.refresh(exam1)
    test_db_session.refresh(exam2)

    assert len(exam1.exam_questions) == 1
    assert len(exam2.exam_questions) == 1
    assert exam1.exam_questions[0].question_id == reusable_question.id
    assert exam2.exam_questions[0].question_id == reusable_question.id
    assert exam1.exam_questions[0].question_id == exam2.exam_questions[0].question_id
