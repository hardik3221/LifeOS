from datetime import date, datetime
from uuid import UUID
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from backend.schemas.entities import TaskRead, GoalRead

class PlannerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    available_start: AwareDatetime
    available_end: AwareDatetime
    @model_validator(mode="after")
    def valid_window(self):
        if self.available_end <= self.available_start:
            raise ValueError("available_end must be after available_start")
        if self.available_start.date() != self.date or self.available_end.date() != self.date:
            raise ValueError("Both window boundaries must fall on date in their supplied offset")
        return self

class ScheduleItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: UUID
    start: AwareDatetime
    end: AwareDatetime
    @model_validator(mode="after")
    def valid_times(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self

class PlannerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    schedule: list[ScheduleItem]
    unscheduled_task_ids: list[UUID] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

class PlannerContext(BaseModel):
    tasks: list[TaskRead]
    goals: list[GoalRead]
