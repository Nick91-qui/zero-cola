from decimal import Decimal
from uuid import UUID

import pytest

from app.models.answer_key import AnswerKey, AnswerKeyItem
from app.models.enums import UserRole
from app.models.omr import OMRTemplate
from app.models.question import Question
from app.models.skill import Skill
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

    assert exam.answer_key is None
    assert len(exam.exam_questions) == 2
    assert [eq.display_order for eq in exam.exam_questions] == [1, 2]
    assert [q.statement for q in exam.questions] == ["Questão 1", "Questão 2"]


def test_publish_exam_projects_workflow_a_snapshot(test_db_session):
    teacher = User(
        email="teacher_publish@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    skill = Skill(
        code="EF05MA01",
        description="Resolve problemas",
        subject="Matemática",
        grade_level="5",
        curriculum="BNCC",
    )
    test_db_session.add_all([teacher, skill])
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Publicação Workflow A",
            total_questions=2,
            questions=[
                ExamQuestionCreate(
                    display_order=2,
                    weight=Decimal("2.00"),
                    question=QuestionCreate(
                        statement="Questão 2",
                        correct_answer="B",
                        options={"A": "A", "B": "B"},
                        skill_ids=[skill.id],
                    ),
                ),
                ExamQuestionCreate(
                    display_order=1,
                    weight=Decimal("1.00"),
                    question=QuestionCreate(
                        statement="Questão 1",
                        correct_answer="A",
                        options={"A": "A", "B": "B"},
                    ),
                ),
            ],
        ),
        teacher_id=teacher.id,
    )

    published_exam = service.publish_exam(exam.id)
    test_db_session.refresh(published_exam)

    assert published_exam.answer_key is not None
    assert published_exam.answer_key.is_published is True
    assert published_exam.answer_key.published_at is not None
    assert [item.item_number for item in published_exam.answer_key.items] == [1, 2]
    assert [item.correct_answer for item in published_exam.answer_key.items] == ["A", "B"]
    assert [item.statement for item in published_exam.answer_key.items] == [
        "Questão 1",
        "Questão 2",
    ]
    assert [item.weight for item in published_exam.answer_key.items] == [
        Decimal("1.00"),
        Decimal("2.00"),
    ]
    assert [item.question_id for item in published_exam.answer_key.items] == [
        published_exam.exam_questions[0].question_id,
        published_exam.exam_questions[1].question_id,
    ]
    assert [skill.code for skill in published_exam.answer_key.items[1].skills] == [
        "EF05MA01"
    ]

    source_question = published_exam.exam_questions[0].question
    source_question.statement = "Questão 1 atualizada"
    source_question.correct_answer = "Z"
    source_question.options = {"A": "A", "Z": "Z"}
    source_question.skills.clear()
    test_db_session.commit()

    refreshed_item = (
        test_db_session.query(AnswerKeyItem)
        .join(AnswerKey)
        .filter(AnswerKey.exam_id == exam.id, AnswerKeyItem.item_number == 1)
        .one()
    )
    assert refreshed_item.statement == "Questão 1"
    assert refreshed_item.correct_answer == "A"
    assert refreshed_item.skills == []


def test_published_answer_key_items_are_immutable(test_db_session):
    teacher = User(
        email="teacher_immutable@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()
    teacher_id = teacher.id

    def create_published_exam(title: str) -> tuple[ExamService, UUID]:
        service = ExamService(test_db_session)
        exam = service.create_exam(
            ExamCreate(
                title=title,
                total_questions=1,
                questions=[
                    ExamQuestionCreate(
                        display_order=1,
                        question=QuestionCreate(
                            statement="Questão",
                            correct_answer="A",
                        ),
                    ),
                ],
            ),
            teacher_id=teacher_id,
        )
        service.publish_exam(exam.id)
        return service, exam.id

    _, exam_id = create_published_exam("Imutabilidade Item")

    item = (
        test_db_session.query(AnswerKeyItem)
        .join(AnswerKey)
        .filter(AnswerKey.exam_id == exam_id)
        .one()
    )
    item.correct_answer = "B"

    with pytest.raises(ValueError, match="immutable"):
        test_db_session.commit()

    test_db_session.rollback()

    _, exam_id = create_published_exam("Imutabilidade AnswerKey")

    answer_key = (
        test_db_session.query(AnswerKey)
        .filter(AnswerKey.exam_id == exam_id)
        .one()
    )
    answer_key.published_at = None

    with pytest.raises(ValueError, match="immutable"):
        test_db_session.commit()

    test_db_session.rollback()

    skill = Skill(
        code="EF05MA02",
        description="Nova skill",
        subject="Matemática",
        grade_level="5",
        curriculum="BNCC",
    )
    test_db_session.add(skill)
    test_db_session.commit()

    _, exam_id = create_published_exam("Imutabilidade Skills")

    item = (
        test_db_session.query(AnswerKeyItem)
        .join(AnswerKey)
        .filter(AnswerKey.exam_id == exam_id)
        .one()
    )
    item.skills.append(skill)

    with pytest.raises(ValueError, match="immutable"):
        test_db_session.commit()


def test_publish_exam_rejects_invalid_workflow_a(test_db_session):
    teacher = User(
        email="teacher_invalid_publish@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = ExamService(test_db_session)
    empty_exam = service.create_exam(ExamCreate(title="Sem questões"), teacher_id=teacher.id)

    with pytest.raises(ValueError, match="no exam_questions"):
        service.publish_exam(empty_exam.id)

    inactive_question = Question(
        statement="Inativa",
        type="multiple_choice",
        correct_answer="A",
        created_by=teacher.id,
        is_active=False,
    )
    test_db_session.add(inactive_question)
    test_db_session.commit()

    inactive_exam = service.create_exam(
        ExamCreate(
            title="Questão inativa",
            total_questions=1,
            questions=[
                ExamQuestionCreate(
                    display_order=1,
                    question_id=inactive_question.id,
                )
            ],
        ),
        teacher_id=teacher.id,
    )

    with pytest.raises(ValueError, match="inactive"):
        service.publish_exam(inactive_exam.id)

    active_question = Question(
        statement="Sequência inválida",
        type="multiple_choice",
        correct_answer="A",
        created_by=teacher.id,
    )
    test_db_session.add(active_question)
    test_db_session.commit()

    invalid_exam = service.create_exam(
        ExamCreate(
            title="Ordem inválida",
            total_questions=2,
            questions=[
                ExamQuestionCreate(display_order=1, question_id=active_question.id),
                ExamQuestionCreate(
                    display_order=2,
                    question=QuestionCreate(
                        statement="Questão complementar",
                        correct_answer="B",
                    ),
                ),
            ],
        ),
        teacher_id=teacher.id,
    )
    invalid_exam.exam_questions[1].display_order = 3
    test_db_session.commit()

    with pytest.raises(ValueError, match="contiguous"):
        service.publish_exam(invalid_exam.id)


def test_publish_workflow_b_answer_key_without_question_bank(test_db_session):
    teacher = User(
        email="teacher_workflow_b_publish@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Workflow B",
            total_questions=2,
            correct_answers={"1": "A", "2": "C"},
        ),
        teacher_id=teacher.id,
    )

    published_exam = service.publish_exam(exam.id)
    test_db_session.refresh(published_exam)

    assert published_exam.answer_key is not None
    assert published_exam.answer_key.is_published is True
    assert [item.question_id for item in published_exam.answer_key.items] == [None, None]


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
