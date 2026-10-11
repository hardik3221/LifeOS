from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.entities import Goal
from backend.schemas.entities import GoalCreate, GoalPatch, GoalRead
from backend.services.crud import get_or_404, save

router = APIRouter(prefix="/api/goals", tags=["goals"])

@router.get("", response_model=list[GoalRead])
def list_goals(offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), completed: bool | None = None, db: Session = Depends(get_db)):
    query = select(Goal).order_by(Goal.created_at, Goal.id).offset(offset).limit(limit)
    if completed is not None:
        query = query.where(Goal.completed == completed)
    return db.scalars(query).all()

@router.post("", response_model=GoalRead, status_code=201)
def create_goals(payload: GoalCreate, db: Session = Depends(get_db)):
    return save(db, Goal, payload)

@router.get("/{resource_id}", response_model=GoalRead)
def read_goals(resource_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, Goal, resource_id)

@router.patch("/{resource_id}", response_model=GoalRead)
def patch_goals(resource_id: UUID, payload: GoalPatch, db: Session = Depends(get_db)):
    return save(db, Goal, payload, get_or_404(db, Goal, resource_id))

@router.delete("/{resource_id}", status_code=204)
def delete_goals(resource_id: UUID, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Goal, resource_id))
    db.commit()
    return Response(status_code=204)
