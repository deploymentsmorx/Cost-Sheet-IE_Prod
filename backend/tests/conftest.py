"""
Test fixtures.

Each test runs inside a savepoint (nested transaction) that is rolled back
after the test, so the seed data is always present and tests are isolated.
"""
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def run_migrations():
    """Ensure schema is up-to-date before tests run."""
    # Tables already exist via Alembic; nothing to do.
    yield


@pytest.fixture()
def db() -> Session:
    """
    Yields a DB session wrapped in a SAVEPOINT.
    Everything done inside the test is rolled back on teardown.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Use nested savepoint so individual test commits don't propagate
    session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """FastAPI TestClient wired to the test DB session."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
