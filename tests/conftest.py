from __future__ import annotations

import os

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("S3_DOCUMENT_BUCKET", "regimpact-test-documents")
os.environ.setdefault(
    "SQS_QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/123456789012/regimpact-jobs",
)

from collections.abc import Generator
from uuid import uuid4

import pytest
from app.config import get_settings
from app.db.session import get_db, reset_engine
from app.main import create_app
from app.services.bedrock import reset_bedrock_client
from app.services.queue import reset_sqs_client
from app.services.storage import reset_s3_client
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class DummyResult:
    def all(self):
        return []


class DummySession:
    def get(self, *_args, **_kwargs):
        return None

    def add(self, _obj) -> None:
        return None

    def flush(self) -> None:
        return None

    def refresh(self, _obj) -> None:
        return None

    def scalar(self, *_args, **_kwargs):
        return None

    def scalars(self, *_args, **_kwargs) -> DummyResult:
        return DummyResult()

    def execute(self, *_args, **_kwargs):
        return None

    def delete(self, _obj) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    reset_s3_client()
    reset_sqs_client()
    reset_bedrock_client()
    yield
    get_settings.cache_clear()
    reset_s3_client()
    reset_sqs_client()
    reset_bedrock_client()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    def override_db() -> Generator[DummySession, None, None]:
        yield DummySession()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def company_header() -> dict[str, str]:
    return {"X-Company-Id": str(uuid4())}


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    test_url = os.environ.get("TEST_DATABASE_URL")
    if not test_url:
        pytest.skip("PostgreSQL is not configured (set TEST_DATABASE_URL)")
    os.environ["DATABASE_URL"] = test_url
    get_settings.cache_clear()
    reset_engine()
    try:
        from app.db.session import get_session_factory
        from sqlalchemy import text

        session = get_session_factory()()
        session.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL is not reachable: {exc}")
    try:
        yield session
        session.rollback()
    finally:
        session.close()
        reset_engine()
