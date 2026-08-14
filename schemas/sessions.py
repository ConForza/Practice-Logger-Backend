from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StartSessionRequest(BaseModel):
    task_id: int | None = Field(default=None, gt=0, examples=[1])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": 1,
            }
        }
    )


class SetCurrentTaskRequest(BaseModel):
    task_id: int = Field(gt=0, examples=[1])


class EndSessionRequest(BaseModel):
    notes: str | None = None


class SessionTask(BaseModel):
    id: int
    title: str
    description: str | None = None
    status: str


class PracticeSession(BaseModel):
    id: int
    user_id: int
    started_at: datetime
    ended_at: datetime | None = None
    duration: int
    notes: str | None = None
    current_task_id: int | None = None
    tasks: list[SessionTask] = Field(default_factory=list)
    status: str

    # Compatibility fields retained while the frontend moves to the richer
    # session shape.
    start_time: datetime
    task_id: int | None = None
    title: str | None = None


class StartSessionResponse(BaseModel):
    id: int
    task_id: int
    title: str
    start_time: datetime
    status: str = "active"


class EndSessionResponse(BaseModel):
    id: int
    task_id: int
    title: str
    duration: int
    start_time: datetime
    notes: str | None = None
    status: str = "completed"
