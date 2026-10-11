from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Description = Annotated[str, StringConstraints(max_length=10000)]
Minutes = Annotated[int, Field(strict=True, ge=1, le=1440)]
Priority = Literal["low", "medium", "high"]

class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")
    @field_validator("deadline", check_fields=False)
    @classmethod
    def utc_deadline(cls, value):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

class GoalCreate(Input):
    title: Title
    description: Description = ""
    deadline: datetime | None = None
    completed: bool = False

class TaskCreate(GoalCreate):
    priority: Priority = "medium"
    estimated_minutes: Minutes = 30
    goal_id: UUID | None = None

class GoalPatch(Input):
    title: Title | None = None
    description: Description | None = None
    deadline: datetime | None = None
    completed: bool | None = None
    @model_validator(mode="after")
    def valid_patch(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field")
        for name in self.model_fields_set - {"deadline", "goal_id"}:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self

class TaskPatch(GoalPatch):
    priority: Priority | None = None
    estimated_minutes: Minutes | None = None
    goal_id: UUID | None = None

class GoalRead(GoalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    @field_validator("created_at", "updated_at")
    @classmethod
    def utc_timestamp(cls, value):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

class TaskRead(GoalRead):
    priority: Priority
    estimated_minutes: Minutes
    goal_id: UUID | None
