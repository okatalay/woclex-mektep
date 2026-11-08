"""Entegrasyon testleri ayrı bir veritabanında (mektep_test) çalışır; geliştirme verisine dokunmaz."""
import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv_min import load_env  # noqa: E402

load_env(ROOT.parent / ".env")
_base = os.environ["DATABASE_URL"]
TEST_URL = _base.rsplit("/", 1)[0] + "/mektep_test"
os.environ["DATABASE_URL"] = TEST_URL  # config import edilmeden önce
os.environ["DATA_DIR"] = str(ROOT / "data" / "test")


def _admin_dsn() -> str:
    return _base.replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0] + "/postgres"


@pytest.fixture(scope="session", autouse=True)
def _database():
    with psycopg.connect(_admin_dsn(), autocommit=True) as c:
        c.execute("DROP DATABASE IF EXISTS mektep_test WITH (FORCE)")
        c.execute("CREATE DATABASE mektep_test")
    subprocess.run([str(ROOT / ".venv/bin/alembic"), "upgrade", "head"], cwd=ROOT, check=True,
                   env={**os.environ, "DATABASE_URL": TEST_URL}, capture_output=True)
    yield


@pytest.fixture()
def db():
    from database import SessionLocal

    s = SessionLocal()
    yield s
    s.rollback()
    s.close()


def new_client():
    from fastapi.testclient import TestClient

    from main import app

    return TestClient(app)


@pytest.fixture()
def client():
    return new_client()


PW = "pw-test-123"


def uname(prefix="u"):
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def register_teacher(c, account_type="individual", username=None, org="Test Kurumu", full_name="Test Eğitmen"):
    body = {"account_type": account_type, "username": username or uname(), "password": PW, "full_name": full_name}
    if account_type == "institution":
        body["organization_name"] = org
    r = c.post("/api/auth/register", json=body)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
def teacher(client):
    """Bireysel eğitmen olarak girişli client."""
    register_teacher(client, "individual")
    return client


@pytest.fixture()
def institution_owner(client):
    register_teacher(client, "institution")
    return client
