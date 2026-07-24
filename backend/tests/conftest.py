import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import BaseModel


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    BaseModel.metadata.create_all(bind=engine)
    yield engine

    BaseModel.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a new database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(test_db_session):
    """Override FastAPI dependency for database session."""
    from app.db.session import get_db
    from app.main import app

    def get_db_override():
        return test_db_session

    app.dependency_overrides[get_db] = get_db_override
    yield
    app.dependency_overrides.clear()
