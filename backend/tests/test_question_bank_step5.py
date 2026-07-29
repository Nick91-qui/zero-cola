from pathlib import Path

from app.models.enums import UserRole
from app.models.question import Question
from app.models.skill import Skill
from app.models.user import User


def test_question_model_is_repurposed_for_bank(test_db_session):
    teacher = User(
        email="teacher_question_bank@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    question = Question(
        statement="Questão do banco",
        type="multiple_choice",
        options={"A": "A", "B": "B"},
        correct_answer="A",
        explanation="Explicação",
        subject="Matemática",
        difficulty="easy",
        created_by=teacher.id,
    )
    test_db_session.add(question)
    test_db_session.commit()

    assert "parent_id" in Question.__table__.c
    assert "version" in Question.__table__.c
    assert "is_active" in Question.__table__.c
    assert "statement" in Question.__table__.c
    assert "type" in Question.__table__.c
    assert "options" in Question.__table__.c
    assert "correct_answer" in Question.__table__.c
    assert "created_by" in Question.__table__.c
    assert "exam_id" not in Question.__table__.c
    assert "question_number" not in Question.__table__.c
    assert "correct_option" not in Question.__table__.c
    assert "weight" not in Question.__table__.c
    assert question.correct_answer == "A"
    assert question.version == 1
    assert question.is_active is True


def test_question_bank_skills_relationship_works(test_db_session):
    teacher = User(
        email="teacher_skill_bank@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    skill = Skill(
        code="EF05MA01",
        description="Resolve problemas",
        subject="Matemática",
        grade_level="5",
        curriculum="BNCC",
    )
    question = Question(
        statement="Questão com skill",
        type="multiple_choice",
        correct_answer="B",
        created_by=teacher.id,
    )
    question.skills.append(skill)
    test_db_session.add_all([skill, question])
    test_db_session.commit()

    test_db_session.refresh(question)
    assert len(question.skills) == 1
    assert question.skills[0].code == "EF05MA01"


def test_step5_migration_source_mentions_legacy_renames() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "d4e5f6a7b8c9_repurpose_questions_to_bank.py"
    )
    source = migration_path.read_text()

    assert 'revision: str = "d4e5f6a7b8c9"' in source
    assert 'down_revision: Union[str, None] = "c3d4e5f6a7b8"' in source
    assert 'op.rename_table("questions", "questions_legacy")' in source
    assert 'op.rename_table("question_skills", "question_skills_legacy")' in source
    assert 'op.create_table(\n        "questions",' in source
    assert 'op.create_table(\n        "question_skills",' in source
