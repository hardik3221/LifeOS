import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.entities import Task, Goal
from backend.schemas.entities import TaskRead, GoalRead
from backend.schemas.planner import PlannerContext, PlannerRequest, PlannerResponse
from backend.services.planner import PlannerService, get_planner

router = APIRouter(prefix="/api/planner", tags=["planner"])
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=PlannerResponse)
def generate(payload: PlannerRequest, db: Session = Depends(get_db), planner: PlannerService = Depends(get_planner)):
    context = PlannerContext(
        tasks=[TaskRead.model_validate(row) for row in db.scalars(select(Task).where(Task.completed.is_(False)).order_by(Task.created_at, Task.id))],
        goals=[GoalRead.model_validate(row) for row in db.scalars(select(Goal).where(Goal.completed.is_(False)).order_by(Goal.created_at, Goal.id))],
    )
    try:
        result = PlannerResponse.model_validate(planner.generate(payload, context))
        known = {task.id for task in context.tasks}
        scheduled = [item.task_id for item in result.schedule]
        unscheduled = result.unscheduled_task_ids
        if result.date != payload.date or set(scheduled + unscheduled) != known:
            raise ValueError("Planner must account for every supplied task")
        if len(set(scheduled + unscheduled)) != len(scheduled + unscheduled):
            raise ValueError("Duplicate task in planner result")
        previous_end = payload.available_start
        for item in sorted(result.schedule, key=lambda item: item.start):
            if item.start < previous_end or item.end > payload.available_end:
                raise ValueError("Overlapping or out-of-window schedule")
            previous_end = item.end
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("AI planner failed")
        raise HTTPException(502, "AI planner failed to produce a valid schedule") from None
