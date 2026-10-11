from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.models.entities import Goal

def get_or_404(db: Session, model, resource_id):
    row = db.get(model, str(resource_id))
    if row is None:
        raise HTTPException(404, f"{model.__name__} not found")
    return row

def save(db: Session, model, payload, row=None):
    values = payload.model_dump(exclude_unset=row is not None)
    if values.get("goal_id") is not None:
        get_or_404(db, Goal, values["goal_id"])
    values = {key: str(value) if isinstance(value, UUID) else value for key, value in values.items()}
    if row is None:
        row = model(**values)
    else:
        for key, value in values.items():
            setattr(row, key, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
