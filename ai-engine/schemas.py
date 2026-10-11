"""Shared data validation and response helpers for the LifeOS AI engine."""
from __future__ import annotations
from datetime import date
from typing import Any


def validate_tasks(tasks: list[dict[str, Any]]) -> None:
    if not isinstance(tasks, list):
        raise TypeError("tasks must be a list of dictionaries")
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise TypeError(f"tasks[{i}] must be a dictionary")
        if not task.get("id") and not task.get("task_id"):
            raise ValueError(f"tasks[{i}] must include 'id' or 'task_id'")
        if not str(task.get("title", "")).strip():
            raise ValueError(f"tasks[{i}] must include a non-empty title")
        duration = task.get("estimated_minutes", task.get("duration_minutes", 30))
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError(f"tasks[{i}] duration must be a positive number")


def task_id(task: dict[str, Any]) -> str:
    return str(task.get("id", task.get("task_id")))


def task_duration(task: dict[str, Any]) -> int:
    return max(1, int(round(task.get("estimated_minutes", task.get("duration_minutes", 30)))))


def normalize_plan_date(value: str | date | None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(value).isoformat()
