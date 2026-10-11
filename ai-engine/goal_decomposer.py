"""Goal decomposition. Deterministic fallback; estimates are explicitly labelled."""
from __future__ import annotations
import re
from typing import Any


def decompose_goal(goal: str, timeframe_days: int) -> dict[str, Any]:
    """Create a small actionable starter breakdown without pretending an LLM was used."""
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be a non-empty string")
    if not isinstance(timeframe_days, int) or timeframe_days < 1:
        raise ValueError("timeframe_days must be a positive integer")
    clean = goal.strip().rstrip(".!?")
    # Split common compound goals into rough action phrases; otherwise provide a reusable workflow.
    pieces = [p.strip(" ,") for p in re.split(r"\b(?:and then|then|and)\b", clean, flags=re.I) if p.strip(" ,")]
    if len(pieces) > 1:
        actions = pieces[:5]
    else:
        actions = [
            f"Define the scope and success criteria for: {clean}",
            f"Break down the work required for: {clean}",
            f"Complete the first major work session for: {clean}",
            f"Review progress and address gaps for: {clean}",
            f"Finish and evaluate: {clean}",
        ]
    count = len(actions)
    tasks = []
    for i, action in enumerate(actions, 1):
        tasks.append({
            "id": f"goal-task-{i}",
            "title": action[0].upper() + action[1:] if action else action,
            "estimated_minutes": 30 if count > 3 else 45,
            "estimate_type": "heuristic_estimate",
            "deadline_offset_days": max(0, round(i * timeframe_days / count) - 1),
            "priority": "high" if i == count else "medium",
            "status": "pending",
        })
    return {
        "goal": clean,
        "timeframe_days": timeframe_days,
        "tasks": tasks,
        "notes": ["Task breakdown and durations are heuristic estimates; review and edit them before relying on the plan."],
        "llm_used": False,
    }
