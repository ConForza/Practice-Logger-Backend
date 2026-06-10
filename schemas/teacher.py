from pydantic import BaseModel

class WeeklyStudentProgress(BaseModel):
    student_id: int
    email: str
    total_duration: int
    session_count: int