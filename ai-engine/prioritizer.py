"""Deterministic, explainable task prioritization."""
from __future__ import annotations
from datetime import date
from typing import Any
from schemas import task_id


def _deadline_days(task: dict[str, Any], today: date) -> int | None:
    raw = task.get("deadline") or task.get("due_date")
    if not raw:
        return None
    try:
        return (date.fromisoformat(str(raw)[:10]) - today).days
    except ValueError:
        return None


def score_task(task: dict[str, Any], today: date | None = None) -> tuple[float, str]:
    """Return (score, explanation). Larger scores are scheduled earlier."""
    today = today or date.today()
    priority = str(task.get("priority", "medium")).lower()
    importance = str(task.get("importance", "medium")).lower()
    priority_points = {"critical": 40, "high": 30, "medium": 20, "low": 10}
    importance_points = {"critical": 30, "high": 22, "medium": 14, "low": 6}
    score = priority_points.get(priority, 20) + importance_points.get(importance, 14)
    reasons = []
    if priority in ("critical", "high"):
        reasons.append(f"{priority.title()} priority")
    if importance in ("critical", "high"):
        reasons.append(f"{importance.title()} importance")
    days = _deadline_days(task, today)
    if days is not None:
        if days < 0:
            score += 50
            reasons.append("Overdue")
        elif days == 0:
            score += 45
            reasons.append("Due today")
        elif days == 1:
            score += 35
            reasons.append("Due tomorrow")
        elif days <= 3:
            score += 22
            reasons.append("Deadline approaching")
        elif days <= 7:
            score += 10
            reasons.append("Due within a week")
    if not reasons:
        reasons.append("Balanced priority and importance")
    return score, "; ".join(reasons)


def prioritize_tasks(tasks: list[dict[str, Any]], plan_date: date | None = None) -> list[dict[str, Any]]:
    """Sort tasks by score, then earlier deadline, preserving input order for ties."""
    today = plan_date or date.today()
    decorated = []
    for index, task in enumerate(tasks):
        score, reason = score_task(task, today)
        days = _deadline_days(task, today)
        decorated.append((-(score), days if days is not None else 99999, index, task, reason))
    decorated.sort(key=lambda item: item[:3])
    result = []
    for _, _, _, task, reason in decorated:
        copy = dict(task)
        copy["_priority_reason"] = reason
        result.append(copy)
    return result
