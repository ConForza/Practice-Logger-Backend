from pydantic import BaseModel, Field, ConfigDict

class TaskRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Moonlight Sonata Practice",
                "description": "Learn bars 1-8 of Moonlight Sonata"
            }
        }
    )

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    status: str
    user_id: int