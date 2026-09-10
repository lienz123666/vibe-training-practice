import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app, get_db

# 测试专用数据库：独立文件，不污染你的 tasks.db
TEST_DATABASE_URL = "sqlite:///./test_tasks.db"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    # 每个测试前重建表，保证互相独立（id 从 1 开始）
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_task_returns_201_with_id():
    r = client.post("/tasks", json={"title": "Learn FastAPI", "description": "Day2"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Learn FastAPI"
    assert body["id"] == 1          # 空表里第一个 id 就是 1
    assert body["completed"] is False


def test_create_missing_title_is_422():
    assert client.post("/tasks", json={}).status_code == 422


def test_create_blank_title_is_400():
    assert client.post("/tasks", json={"title": "   "}).status_code == 400


def test_get_nonexistent_task_is_404():
    assert client.get("/tasks/999").status_code == 404


def test_update_nonexistent_task_is_404():
    r = client.put("/tasks/999", json={"title": "x", "completed": True})
    assert r.status_code == 404


def test_delete_returns_204_then_404():
    task_id = client.post("/tasks", json={"title": "to delete"}).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_completed_filter():
    # 先建两条，再把其中一条通过 PUT 改成 completed=True
    t1 = client.post("/tasks", json={"title": "finish me"}).json()["id"]
    client.post("/tasks", json={"title": "leave open"})
    client.put(f"/tasks/{t1}", json={"title": "finish me", "completed": True})
    done = client.get("/tasks", params={"completed": True}).json()
    open_ = client.get("/tasks", params={"completed": False}).json()
    assert len(done) == 1 and done[0]["id"] == t1
    assert len(open_) == 1


def test_limit():
    for i in range(3):
        client.post("/tasks", json={"title": f"task {i}"})
    assert len(client.get("/tasks", params={"limit": 2}).json()) == 2
    assert client.get("/tasks", params={"limit": 0}).status_code == 422
    assert client.get("/tasks", params={"limit": 101}).status_code == 422


def test_stats():
    t1 = client.post("/tasks", json={"title": "a"}).json()["id"]
    client.post("/tasks", json={"title": "b"})
    client.put(f"/tasks/{t1}", json={"title": "a", "completed": True})
    stats = client.get("/stats").json()
    assert stats == {"total": 2, "completed": 1, "pending": 1}
