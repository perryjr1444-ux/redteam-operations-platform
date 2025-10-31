"""Pytest fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.database import Base
from app.config import settings
# Import models to ensure they're registered with Base metadata
from app import models  # noqa: F401


# Test database - use file:memdb?mode=memory&cache=shared to ensure
# all connections use the same in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///file:memdb?mode=memory&cache=shared&uri=true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
    poolclass=None  # Disable pooling for in-memory shared database
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_template():
    """Sample template data."""
    return {
        "template_id": "test-001",
        "name": "Test Template",
        "category": "detection",
        "risk_level": "medium",
        "duration": "2h",
    }


@pytest.fixture
def sample_exercise():
    """Sample exercise data."""
    return {
        "exercise_id": "ex-20250101-001",
        "template": "test-001",
        "state": "draft",
        "progress": 0.0,
        "start_date": "2025-01-01",
        "owner": "testuser",
    }
