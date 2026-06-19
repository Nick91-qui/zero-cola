from app.db.models import BaseModel


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
