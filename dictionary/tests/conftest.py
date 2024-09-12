"""Note: a postgresql database for tests must be created first (empty database)."""

import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["ENV_STATE"] = "test"

from dictionary.config import config
from dictionary.database import Base, get_db
from dictionary.main import app

# Creating testing database instead of using prod/dev database
engine = create_engine(config.DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Overriding database connection for all of the endpoins
@pytest.fixture
def db_session():
    """Sets a clean db session for each test."""

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Creating test clients
@pytest.fixture
def client(db_session) -> Generator:
    """Yield TestClient() on tested app."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)


@pytest.fixture
async def async_client(client) -> AsyncGenerator:
    """Uses async client from httpx instead of test client from fastapi for async tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=client.base_url,
    ) as ac:
        yield ac


# Overriding fixture pytest.mark.anyio to test async functions
@pytest.fixture(scope="session")
def anyio_backend():
    """
    Overrides anyio.pytest_plugin fixture to return asyncio
    as a designated library for async fixtures.
    """
    return "asyncio"
