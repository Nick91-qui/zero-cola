import asyncio

import pytest
from fastapi import HTTPException

from app.api.routes.questions import create_question, get_question, list_questions
from app.models.enums import UserRole
from app.models.question import Question
from app.models.skill import Skill
from app.models.user import User
from app.schemas.exam import QuestionCreate


def test_teacher_can_create_and_list_questions(test_db_session):
    teacher = User(
        email="teacher_questions@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    created = asyncio.run(
        create_question(
            question_in=QuestionCreate(
                statement="Quanto é 2 + 2?",
                type="multiple_choice",
                options={
                    "A": "3",
                    "B": "4",
                    "C": "5",
                },
                correct_answer="B",
                subject="Matemática",
                difficulty="easy",
                tags=["aritmética"],
            ),
            current_user=teacher,
            db=test_db_session,
        )
    )

    assert created["statement"] == "Quanto é 2 + 2?"
    assert created["correct_answer"] == "B"
    assert created["is_active"] is True
    assert created["skills"] == []

    payload = asyncio.run(
        list_questions(
            q="",
            skill_id=None,
            include_inactive=False,
            skip=0,
            limit=100,
            current_user=teacher,
            db=test_db_session,
        )
    )
    assert len(payload) == 1
    assert payload[0]["id"] == created["id"]

    detail = asyncio.run(
        get_question(
            question_id=created["id"],
            current_user=teacher,
            db=test_db_session,
        )
    )
    assert detail["id"] == created["id"]


def test_student_cannot_access_question_bank(test_db_session):
    student = User(
        email="student_questions@cola-zero.edu",
        password_hash="hash",
        role=UserRole.STUDENT,
        student_code="11223",
    )
    test_db_session.add(student)
    test_db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            list_questions(
                q="",
                skill_id=None,
                include_inactive=False,
                skip=0,
                limit=100,
                current_user=student,
                db=test_db_session,
            )
        )

    assert exc_info.value.status_code == 403


def test_teacher_can_filter_question_bank_by_text_skill_status_and_pagination(test_db_session):
    teacher = User(
        email="teacher_questions_filters@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    skill = Skill(
        code="EF05MA01",
        description="Resolver adições simples",
        subject="Matemática",
    )
    test_db_session.add_all([teacher, skill])
    test_db_session.commit()

    question_a = asyncio.run(
        create_question(
            question_in=QuestionCreate(
                statement="Questão com frações",
                type="multiple_choice",
                options={"A": "1", "B": "2", "C": "3"},
                correct_answer="B",
                subject="Matemática",
                difficulty="easy",
                tags=["aritmética"],
                skill_ids=[skill.id],
            ),
            current_user=teacher,
            db=test_db_session,
        )
    )
    question_b = asyncio.run(
        create_question(
            question_in=QuestionCreate(
                statement="Questão de geometria",
                type="multiple_choice",
                options={"A": "4", "B": "5", "C": "6"},
                correct_answer="C",
                subject="Matemática",
                difficulty="medium",
            ),
            current_user=teacher,
            db=test_db_session,
        )
    )
    question_c = asyncio.run(
        create_question(
            question_in=QuestionCreate(
                statement="Questão desativada",
                type="multiple_choice",
                options={"A": "7", "B": "8", "C": "9"},
                correct_answer="A",
                subject="História",
                difficulty="hard",
            ),
            current_user=teacher,
            db=test_db_session,
        )
    )

    inactive_question = test_db_session.get(Question, question_c["id"])
    assert inactive_question is not None
    inactive_question.is_active = False
    test_db_session.commit()

    filtered = asyncio.run(
        list_questions(
            q="Resolver",
            skill_id=skill.id,
            include_inactive=False,
            skip=0,
            limit=100,
            current_user=teacher,
            db=test_db_session,
        )
    )
    assert [item["id"] for item in filtered] == [question_a["id"]]

    page = asyncio.run(
        list_questions(
            q="",
            skill_id=None,
            include_inactive=True,
            skip=1,
            limit=1,
            current_user=teacher,
            db=test_db_session,
        )
    )
    assert len(page) == 1
    assert page[0]["id"] == question_b["id"]
