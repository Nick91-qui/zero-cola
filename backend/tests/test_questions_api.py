import asyncio

import pytest
from fastapi import HTTPException

from app.api.routes.questions import create_question, get_question, list_questions
from app.models.enums import UserRole
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
