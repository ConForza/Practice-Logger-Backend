from pydantic import BaseModel, ConfigDict, Field

class TeacherStudentLinkCreate(BaseModel):
    teacher_id: int
    student_id: int
    instrument: str = Field(min_length=1)

class TeacherStudentLinkResponse(BaseModel):
    id: int
    teacher_id: int
    student_id: int
    instrument: str

    model_config = ConfigDict(from_attributes=True)