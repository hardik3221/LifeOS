from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.entities import Task
from backend.schemas.entities import TaskCreate, TaskPatch, TaskRead
from backend.services.crud import get_or_404, save

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("", response_model=list[TaskRead])
def list_tasks(offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), completed: bool | None = None, db: Session = Depends(get_db)):
    query = select(Task).order_by(Task.created_at, Task.id).offset(offset).limit(limit)
    if completed is not None:
        query = query.where(Task.completed == completed)
    return db.scalars(query).all()

@router.post("", response_model=TaskRead, status_code=201)
def create_tasks(payload: TaskCreate, db: Session = Depends(get_db)):
    return save(db, Task, payload)

@router.get("/{resource_id}", response_model=TaskRead)
def read_tasks(resource_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, Task, resource_id)

@router.patch("/{resource_id}", response_model=TaskRead)
def patch_tasks(resource_id: UUID, payload: TaskPatch, db: Session = Depends(get_db)):
    return save(db, Task, payload, get_or_404(db, Task, resource_id))

@router.delete("/{resource_id}", status_code=204)
def delete_tasks(resource_id: UUID, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Task, resource_id))
    db.commit()
    return Response(status_code=204)
