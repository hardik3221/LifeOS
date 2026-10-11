from datetime import datetime, timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.main import create_app
from backend.schemas.planner import PlannerResponse, ScheduleItem

@pytest.fixture
def client():
    app = create_app(Settings(database_url="sqlite:///:memory:", _env_file=None))
    with TestClient(app) as test_client:
        yield test_client

@pytest.mark.parametrize("resource", ["tasks", "goals"])
def test_crud(client, resource):
    url = f"/api/{resource}"
    assert client.get(url).json() == []
    response = client.post(url, json={"title": "  Study arrays  ", "deadline": "2026-10-12T18:00:00+05:30"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Study arrays"
    assert data["deadline"] == "2026-10-12T12:30:00Z"
    assert data["completed"] is False
    detail_url = f"{url}/{data['id']}"
    assert client.get(detail_url).json() == data
    response = client.patch(detail_url, json={"completed": True, "deadline": None})
    assert response.status_code == 200
    assert response.json()["deadline"] is None
    assert response.json()["title"] == "Study arrays"
    assert response.json()["updated_at"] >= data["updated_at"]
    assert len(client.get(url, params={"completed": True}).json()) == 1
    assert client.get(url, params={"completed": False}).json() == []
    assert client.delete(detail_url).status_code == 204
    for response in [client.get(detail_url), client.patch(detail_url, json={"title": "x"}), client.delete(detail_url)]:
        assert response.status_code == 404
        assert response.json()["error"]["message"].endswith("not found")

@pytest.mark.parametrize("resource", ["tasks", "goals"])
@pytest.mark.parametrize("payload", [{}, {"title": " "}, {"title": "x" * 201}, {"title": "x", "bogus": 1}, {"title": "x", "deadline": "tomorrow"}, {"title": "x", "description": "x" * 10001}])
def test_invalid_create(client, resource, payload):
    response = client.post(f"/api/{resource}", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["details"]

@pytest.mark.parametrize("payload", [{"priority": "urgent"}, {"estimated_minutes": 0}, {"estimated_minutes": 1441}, {"estimated_minutes": 1.5}, {"estimated_minutes": True}, {"goal_id": "invalid"}])
def test_invalid_task_fields(client, payload):
    assert client.post("/api/tasks", json={"title": "x", **payload}).status_code == 422

@pytest.mark.parametrize("resource", ["tasks", "goals"])
@pytest.mark.parametrize("payload", [{}, {"title": None}, {"description": None}, {"completed": None}, {"surprise": "x"}])
def test_invalid_patch(client, resource, payload):
    item = client.post(f"/api/{resource}", json={"title": "x"}).json()
    assert client.patch(f"/api/{resource}/{item['id']}", json=payload).status_code == 422
    assert client.get(f"/api/{resource}/{item['id']}").json()["title"] == "x"

@pytest.mark.parametrize("payload", [{"priority": None}, {"estimated_minutes": None}])
def test_task_patch_nulls(client, payload):
    task = client.post("/api/tasks", json={"title": "x"}).json()
    assert client.patch(f"/api/tasks/{task['id']}", json=payload).status_code == 422

def test_goal_relationship(client):
    assert client.post("/api/tasks", json={"title": "x", "goal_id": str(uuid4())}).status_code == 404
    goal = client.post("/api/goals", json={"title": "Learn DSA"}).json()
    task = client.post("/api/tasks", json={"title": "Arrays", "goal_id": goal["id"]}).json()
    assert task["goal_id"] == goal["id"]
    assert client.patch(f"/api/tasks/{task['id']}", json={"goal_id": str(uuid4())}).status_code == 404
    assert client.delete(f"/api/goals/{goal['id']}").status_code == 204
    assert client.get(f"/api/tasks/{task['id']}").json()["goal_id"] is None

def test_clear_goal_link(client):
    goal = client.post("/api/goals", json={"title": "goal"}).json()
    task = client.post("/api/tasks", json={"title": "task", "goal_id": goal["id"]}).json()
    assert client.patch(f"/api/tasks/{task['id']}", json={"goal_id": None}).json()["goal_id"] is None

def test_pagination_and_ids(client):
    for title in ["one", "two", "three"]:
        assert client.post("/api/tasks", json={"title": title}).status_code == 201
    assert len(client.get("/api/tasks?offset=1&limit=1").json()) == 1
    for suffix in ["?offset=-1", "?limit=501", "?limit=0", "/not-a-uuid"]:
        assert client.get("/api/tasks" + suffix).status_code == 422

def test_health_docs_cors(client):
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
    assert client.get("/docs").status_code == 200
    assert "/api/planner/generate" in client.get("/openapi.json").json()["paths"]
    headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"}
    response = client.options("/api/tasks", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == headers["Origin"]
    headers["Origin"] = "https://untrusted.example"
    assert client.options("/api/tasks", headers=headers).status_code == 400

def test_database_persists_across_apps(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'persistent.db'}", _env_file=None)
    with TestClient(create_app(settings)) as first:
        task = first.post("/api/tasks", json={"title": "Persisted task"}).json()
        goal = first.post("/api/goals", json={"title": "Persisted goal"}).json()
    with TestClient(create_app(settings)) as second:
        assert second.get(f"/api/tasks/{task['id']}").json()["title"] == "Persisted task"
        assert second.get(f"/api/goals/{goal['id']}").json()["title"] == "Persisted goal"

WINDOW = {"date": "2026-10-12", "available_start": "2026-10-12T09:00:00+05:30", "available_end": "2026-10-12T18:00:00+05:30"}

def test_unconfigured_planner(client):
    response = client.post("/api/planner/generate", json=WINDOW)
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "AI planner is not configured"

@pytest.mark.parametrize("change", [{"available_end": WINDOW["available_start"]}, {"available_start": "2026-10-12T09:00:00"}, {"date": "2026-10-13"}])
def test_invalid_planner_request(client, change):
    assert client.post("/api/planner/generate", json={**WINDOW, **change}).status_code == 422

class TestPlanner:
    __test__ = False
    def generate(self, request, context):
        self.context = context
        return PlannerResponse(date=request.date, schedule=[], unscheduled_task_ids=[task.id for task in context.tasks])

def test_planner_adapter(client):
    service = TestPlanner()
    client.app.state.planner = service
    pending = client.post("/api/tasks", json={"title": "pending"}).json()
    client.post("/api/tasks", json={"title": "done", "completed": True})
    client.post("/api/goals", json={"title": "goal"})
    response = client.post("/api/planner/generate", json=WINDOW)
    assert response.status_code == 200
    assert response.json()["unscheduled_task_ids"] == [pending["id"]]
    assert len(service.context.tasks) == 1
    assert len(service.context.goals) == 1

@pytest.mark.parametrize("mode", ["raises", "unknown", "missing", "overlap", "outside", "duplicate", "date"])
def test_planner_bad_output(client, mode):
    task = client.post("/api/tasks", json={"title": "x"}).json()
    class BrokenPlanner:
        def generate(self, request, context):
            if mode == "raises":
                raise RuntimeError("secret provider error")
            item = {"task_id": task["id"], "start": request.available_start, "end": request.available_end}
            result = {"date": request.date, "schedule": [item], "unscheduled_task_ids": []}
            if mode == "unknown": item["task_id"] = uuid4()
            if mode == "missing": result["schedule"] = []
            if mode == "overlap":
                second = context.tasks[1].id
                result["schedule"].append({**item, "task_id": second})
            if mode == "outside": item["start"] = datetime(2026, 10, 11, tzinfo=timezone.utc)
            if mode == "duplicate": result["unscheduled_task_ids"] = [task["id"]]
            if mode == "date": result["date"] = "2026-10-13"
            return result
    if mode == "overlap": client.post("/api/tasks", json={"title": "second"})
    client.app.state.planner = BrokenPlanner()
    response = client.post("/api/planner/generate", json=WINDOW)
    assert response.status_code == 502
    assert "secret" not in response.text

def test_valid_schedule(client):
    task = client.post("/api/tasks", json={"title": "x"}).json()
    class Adapter:
        def generate(self, request, context):
            return PlannerResponse(date=request.date, schedule=[ScheduleItem(task_id=task["id"], start=request.available_start, end=request.available_end)])
    client.app.state.planner = Adapter()
    assert client.post("/api/planner/generate", json=WINDOW).status_code == 200
