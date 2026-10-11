# LifeOS AI Engine

Standalone Python planning logic for the LifeOS backend. This package does not create a web server, frontend, or database connection.

## Requirements
- Python 3.10+
- No third-party packages required for the deterministic baseline

## Setup
From the repository root, create `ai-engine/`, then place these files inside it.

```bash
cd ai-engine
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Interface

```python
from planner import generate_daily_plan, reschedule_tasks
from goal_decomposer import decompose_goal
from assistant import process_chat_message

plan = generate_daily_plan(tasks, available_minutes=120, start_time="09:00")
goal = decompose_goal("Prepare for my DBMS exam", timeframe_days=5)
response = process_chat_message(
    "Plan my day",
    {"tasks": tasks, "available_minutes": 120},
)
```

Task input shape (minimum):
```python
{
    "id": "task-1",
    "title": "Practice DSA",
    "estimated_minutes": 60,
    "priority": "high",       # low, medium, high, critical
    "importance": "high",     # low, medium, high, critical
    "deadline": "2026-10-12", # optional ISO date
    "status": "pending",      # completed tasks are not scheduled
    "dependencies": []        # optional list of task IDs
}
```

Planner output is JSON-compatible and contains `plan_date`, `available_minutes`, `total_planned_minutes`, `remaining_minutes`, `schedule`, `unscheduled_tasks`, and `notes`.

## Important behavior
- The total scheduled duration never exceeds `available_minutes`.
- Tasks are scheduled sequentially, so they do not overlap.
- Completed/done/cancelled tasks are excluded.
- Tasks with unmet dependencies are left unscheduled.
- The planner never claims that a task was completed.
- Goal durations and task breakdowns are estimates, not facts.
- The chatbot router is a deterministic baseline, not a full natural-language model. It routes simple intents and returns a prompt for unsupported requests.
- No external LLM API is required for this baseline.

## Integration boundary
The backend owns FastAPI endpoints, authentication, database reads/writes, and task mutations. Call these functions from backend service code and serialize the returned dictionaries. Confirm field names and date/time conventions with the backend developer before integration.

## Known MVP limitations
- Scheduling currently packs tasks back-to-back and does not yet add breaks or calendar events.
- Dependencies are considered satisfied when the referenced task is marked completed in the provided input.
- Goal decomposition is a heuristic fallback; an LLM can be added behind the same output contract later.
