from app.models.user import User


def test_user_model_uses_expected_table_name() -> None:
    assert User.__tablename__ == "users"


def test_user_model_has_expected_columns() -> None:
    table = User.__table__

    assert "email" in table.c
    assert "password_hash" in table.c
    assert "role" in table.c
    assert table.c.email.unique is True
