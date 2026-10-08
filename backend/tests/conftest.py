import os

os.environ["DATABASE_URL"] = "sqlite://"  # never touch the dev DB from tests
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.database import Base, get_db
from app.core.fts import create_fts
from app.main import app
from app.models import User

TRANSCRIPT = """[00:02] Ankit: Let's discuss the backend architecture and the launch deadline.
[00:08] Rahul: I think FastAPI would work well here. I'll write the API spec by Friday.
[00:20] Ankit: We decided to go with SQLite for the demo. What about search performance?
[00:31] Rahul: We need to benchmark FTS5 before the release."""


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        create_fts(conn)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as s:
        s.add(User(id=1, name="Demo User", email="demo@example.com"))
        s.commit()

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def meeting(client):
    r = client.post("/api/v1/meetings", json={"title": "Architecture Sync", "tags": ["eng"], "transcript_text": TRANSCRIPT})
    assert r.status_code == 201, r.text
    return r.json()
