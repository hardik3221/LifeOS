from typing import Protocol
from fastapi import HTTPException, Request
from backend.schemas.planner import PlannerContext, PlannerRequest, PlannerResponse

class PlannerService(Protocol):
    """Developer 3 supplies this adapter; no database writes or LLM here."""
    def generate(self, request: PlannerRequest, context: PlannerContext) -> PlannerResponse: ...

class UnconfiguredPlanner:
    def generate(self, request: PlannerRequest, context: PlannerContext) -> PlannerResponse:
        raise HTTPException(503, "AI planner is not configured")

def get_planner(request: Request) -> PlannerService:
    return request.app.state.planner
