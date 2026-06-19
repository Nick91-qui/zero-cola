from app.core.config import settings
from app.db.session import engine


def test_database_url_uses_psycopg_driver() -> None:
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_database_engine_uses_configured_url() -> None:
    assert str(engine.url.render_as_string(hide_password=False)) == settings.database_url
