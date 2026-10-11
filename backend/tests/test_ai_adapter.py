"""Contract tests for the Developer 3 adapter (engine output mocked)."""
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4

from backend.schemas.entities import TaskRead
from backend.schemas.planner import PlannerContext, PlannerRequest
from backend.services.ai_adapter import AIEnginePlanner


def test_ai_adapter_maps_request_and_result():
    adapter = object.__new__(AIEnginePlanner)
    calls = {}

    def fake_engine(tasks, available_minutes, plan_date, start_time):
        calls.update(tasks=tasks, minutes=available_minutes, date=plan_date, start=start_time)
        return {
            "schedule": [{
                "task_id": tasks[0]["id"],
                "start_time": "09:01", "end_time": "10:01",
            }],
            "unscheduled_tasks": [],
            "notes": ["Planned"],
        }

    adapter.generate_daily_plan = fake_engine
    now = datetime(2026, 10, 11, tzinfo=timezone.utc)
    task = TaskRead(
        id=uuid4(), title="Study", description="", priority="high",
        estimated_minutes=60, deadline=None, completed=False,
        goal_id=None, created_at=now, updated_at=now,
    )
    request = PlannerRequest(
        date=date(2026, 10, 12),
        available_start=datetime(2026, 10, 12, 9, 0, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))),
        available_end=datetime(2026, 10, 12, 11, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))),
    )
    result = adapter.generate(request, PlannerContext(tasks=[task], goals=[]))
    assert calls["minutes"] == 119
    assert calls["start"] == "09:01"
    assert calls["date"] == "2026-10-12"
    assert calls["tasks"][0]["id"] == str(task.id)
    assert calls["tasks"][0]["status"] == "pending"
    assert result.schedule[0].task_id == task.id
    assert result.schedule[0].start.hour == 9
    assert result.notes == ["Planned"]


def test_ai_adapter_accounts_for_unscheduled():
    adapter = object.__new__(AIEnginePlanner)
    adapter.generate_daily_plan = lambda tasks, **kwargs: {
        "schedule": [],
        "unscheduled_tasks": [{"task_id": t["id"]} for t in tasks],
        "notes": [],
    }
    now = datetime(2026, 10, 11, tzinfo=timezone.utc)
    task = TaskRead(id=uuid4(), title="Task", description="", priority="medium",
                    estimated_minutes=30, completed=False, deadline=None,
                    goal_id=None, created_at=now, updated_at=now)
    request = PlannerRequest(date=date(2026, 10, 12),
                             available_start="2026-10-12T09:00:00+05:30",
                             available_end="2026-10-12T10:00:00+05:30")
    result = adapter.generate(request, PlannerContext(tasks=[task], goals=[]))
    assert result.unscheduled_task_ids == [task.id]
