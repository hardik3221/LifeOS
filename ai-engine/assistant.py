
"""Chatbot intent router for the LifeOS AI engine."""
from __future__ import annotations

from typing import Any

from planner import generate_daily_plan, reschedule_tasks
from goal_decomposer import decompose_goal
from gemini_client import generate_ai_reply


FALLBACK_REPLY = (
    "I can help break a goal into tasks, plan your day, "
    "or reschedule unfinished work. Tell me your goal or "
    "provide your pending tasks and available minutes."
)


def process_chat_message(
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Route planning requests locally and general conversation to Gemini."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message must be a non-empty string")

    context = context or {}
    text = message.strip()
    lower = text.lower()

    if any(
        word in lower
        for word in ("reschedule", "replan", "less time", "ran out of time")
    ):
        tasks = context.get("tasks", [])
        minutes = context.get("available_minutes", 0)

        return {
            "intent": "reschedule_tasks",
            "result": reschedule_tasks(tasks, minutes),
            "reply": (
                "I've prepared a revised plan. Review the scheduled "
                "and unscheduled tasks below."
            ),
        }

    if any(
        word in lower
        for word in ("plan my day", "make a plan", "daily plan", "schedule my tasks")
    ):
        tasks = context.get("tasks", [])
        minutes = context.get("available_minutes", 0)

        return {
            "intent": "generate_daily_plan",
            "result": generate_daily_plan(tasks, minutes),
            "reply": (
                "Here's a plan based on your pending tasks "
                "and available time."
            ),
        }

    if any(
        word in lower
        for word in ("goal", "learn", "prepare for", "finish", "build")
    ):
        days = int(context.get("timeframe_days", 7))

        return {
            "intent": "decompose_goal",
            "result": decompose_goal(text, days),
            "reply": (
                "I've broken this goal into starter tasks. Durations "
                "are estimates, so adjust them to your situation."
            ),
        }

    # General conversation: use Gemini.
    try:
        reply = generate_ai_reply(text)
        return {
            "intent": "chat",
            "result": None,
            "reply": reply,
        }
    except Exception:
        # Keep the chatbot usable if the API is unavailable.
        return {
            "intent": "unknown",
            "result": None,
            "reply": FALLBACK_REPLY,
        }
