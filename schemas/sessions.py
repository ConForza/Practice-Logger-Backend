from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class StartSessionRequest(BaseModel):
    task_id: int = Field(gt=0, examples=[1])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": 1,
            }
        }
    )

class StartSessionResponse(BaseModel):
    id: int
    task_id: int
    title: str
    start_time: datetime
    status: str = "active"

class EndSessionRequest(BaseModel):
    notes: str | None = None

class EndSessionResponse(BaseModel):
    id: int
    task_id: int
    title: str
    duration: int
    start_time: datetime
    notes: str | None = None
    status: str = "completed"

class PracticeSession(BaseModel):
    id: int
    duration: int
    notes: str | None = None
    start_time: datetime
    task_id: int