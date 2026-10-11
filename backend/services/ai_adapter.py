"""Adapter for Developer 3's existing ai-engine/planner.py.

The AI branch must be merged into the project before this adapter is enabled.
This module contains no scheduling or LLM logic.
"""
from datetime import datetime, timedelta
from importlib import util
from pathlib import Path
import sys

from backend.schemas.planner import PlannerResponse


class AIEnginePlanner:
    def __init__(self, engine_dir: Path | None = None):
        self.engine_dir = engine_dir or Path(__file__).resolve().parents[2] / "ai-engine"
        file = self.engine_dir / "planner.py"
        if not file.is_file():
            raise FileNotFoundError(f"AI engine not present: {file}")
        # The AI module uses sibling imports: schemas and prioritizer.
        path = str(self.engine_dir)
        if path not in sys.path:
            sys.path.insert(0, path)
        spec = util.spec_from_file_location("lifeos_ai_engine_planner", file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load AI engine: {file}")
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.generate_daily_plan = module.generate_daily_plan

    def generate(self, request, context) -> PlannerResponse:
        start, end = request.available_start, request.available_end
        # AI engine accepts whole-minute availability and HH:MM start times.
        # Floor to the next whole minute so the generated plan stays in bounds.
        aligned = start.replace(second=0, microsecond=0)
        if aligned < start:
            aligned += timedelta(minutes=1)
        budget = max(0, int((end - aligned).total_seconds() // 60))
        tasks = [
            {
                "id": str(t.id), "title": t.title,
                "estimated_minutes": t.estimated_minutes,
                "priority": t.priority,
                "deadline": t.deadline.date().isoformat() if t.deadline else None,
                "status": "pending",
            }
            for t in context.tasks
        ]
        raw = self.generate_daily_plan(
            tasks,
            available_minutes=budget,
            plan_date=request.date.isoformat(),
            start_time=aligned.strftime("%H:%M"),
        )
        zone = start.tzinfo
        schedule = []
        # The AI returns wall-clock HH:MM values. Convert using the requested
        # window's time zone; enforce physical bounds in the route validator.
        for slot in raw["schedule"]:
            begin = datetime.combine(request.date, datetime.strptime(slot["start_time"], "%H:%M").time(), tzinfo=zone)
            finish = datetime.combine(request.date, datetime.strptime(slot["end_time"], "%H:%M").time(), tzinfo=zone)
            if finish <= begin:
                finish += timedelta(days=1)
            schedule.append({"task_id": slot["task_id"], "start": begin, "end": finish})
        return PlannerResponse(
            date=request.date,
            schedule=schedule,
            unscheduled_task_ids=[item["task_id"] for item in raw["unscheduled_tasks"]],
            notes=raw.get("notes", []),
        )
