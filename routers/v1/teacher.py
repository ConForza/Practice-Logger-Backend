from fastapi import APIRouter, Depends

from core.auth import require_teacher
from core.deps import get_teacher_service
from schemas.auth import UserResponse
from schemas.sessions import PracticeSession
from schemas.tasks import TaskResponse, TaskRequest
from services.teacher_service import TeacherService

router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"],
)


@router.get("/status")
async def teacher_status(
    current_user: UserResponse = Depends(require_teacher),
):
    return {
        "message": "Teacher router is working",
        "user": current_user,
    }

@router.get("/students", response_model=list[UserResponse])
async def get_teacher_students(
    current_user: UserResponse = Depends(require_teacher),
    teacher_service: TeacherService = Depends(get_teacher_service),
):
    return teacher_service.get_students()

@router.get(
    "/students/{student_id}/sessions",
    response_model=list[PracticeSession],
)
async def get_student_sessions_for_teacher(
    student_id: int,
    current_user: UserResponse = Depends(require_teacher),
    teacher_service: TeacherService = Depends(get_teacher_service),
):
    return teacher_service.get_student_sessions(student_id)

@router.post(
    "/students/{student_id}/tasks",
    response_model=TaskResponse,
)
async def assign_task_to_student(
    student_id: int,
    task_data: TaskRequest,
    current_user: UserResponse = Depends(require_teacher),
    teacher_service: TeacherService = Depends(get_teacher_service),
):
    return teacher_service.assign_task_to_student(task_data, student_id)