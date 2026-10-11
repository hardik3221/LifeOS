"""Deterministic daily scheduling and rescheduling for LifeOS."""
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Any
from schemas import normalize_plan_date, task_duration, task_id, validate_tasks
from prioritizer import prioritize_tasks


def generate_daily_plan(
    tasks: list[dict[str, Any]],
    available_minutes: int,
    plan_date: str | date | None = None,
    start_time: str = "09:00",
) -> dict[str, Any]:
    """Create a non-overlapping schedule. Durations are never allowed to exceed the time budget."""
    validate_tasks(tasks)
    if not isinstance(available_minutes, int) or available_minutes < 0:
        raise ValueError("available_minutes must be a non-negative integer")
    try:
        cursor = datetime.strptime(start_time, "%H:%M")
    except ValueError as exc:
        raise ValueError("start_time must use HH:MM, e.g. '09:00'") from exc
    plan_day = normalize_plan_date(plan_date)
    day = date.fromisoformat(plan_day)
    eligible = [t for t in tasks if str(t.get("status", "pending")).lower() not in {"completed", "done", "cancelled"}]
    ordered = prioritize_tasks(eligible, day)
    schedule, unscheduled = [], []
    used = 0
    for task in ordered:
        duration = task_duration(task)
        dependencies = task.get("dependencies", []) or []
        completed_ids = {task_id(t) for t in tasks if str(t.get("status", "")).lower() in {"completed", "done"}}
        unmet = [str(dep) for dep in dependencies if str(dep) not in completed_ids]
        if unmet:
            unscheduled.append({
                "task_id": task_id(task), "title": task["title"],
                "duration_minutes": duration, "reason": "Blocked by incomplete dependencies",
                "blocked_by": unmet,
            })
            continue
        if used + duration > available_minutes:
            unscheduled.append({
                "task_id": task_id(task), "title": task["title"],
                "duration_minutes": duration, "reason": "Does not fit in the remaining available time",
            })
            continue
        start = cursor
        end = start + timedelta(minutes=duration)
        schedule.append({
            "task_id": task_id(task),
            "title": task["title"],
            "start_time": start.strftime("%H:%M"),
            "end_time": end.strftime("%H:%M"),
            "duration_minutes": duration,
            "reason": task["_priority_reason"],
        })
        cursor = end
        used += duration
    notes = []
    if unscheduled:
        notes.append(f"{len(unscheduled)} task(s) could not be scheduled within the available time or have unmet dependencies.")
    if available_minutes == 0 and eligible:
        notes.append("No planning time is available; all pending tasks remain unscheduled.")
    return {
        "plan_date": plan_day,
        "available_minutes": available_minutes,
        "total_planned_minutes": used,
        "remaining_minutes": available_minutes - used,
        "schedule": schedule,
        "unscheduled_tasks": unscheduled,
        "notes": notes,
    }


def reschedule_tasks(
    tasks: list[dict[str, Any]],
    available_minutes: int,
    plan_date: str | date | None = None,
    start_time: str = "09:00",
) -> dict[str, Any]:
    """Replan unfinished tasks using the same deterministic rules."""
    unfinished = [dict(t) for t in tasks if str(t.get("status", "pending")).lower() not in {"completed", "done", "cancelled"}]
    return generate_daily_plan(unfinished, available_minutes, plan_date, start_time)
