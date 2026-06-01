from fastapi import APIRouter, Depends

from core.auth import require_teacher
from schemas.auth import UserResponse
from sqlalchemy.orm import Session
from core.deps import get_db
from repositories.user_repository import UserRepository
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
    db: Session = Depends(get_db),
):
    user_repo = UserRepository(db)
    teacher_service = TeacherService(user_repo)
    return teacher_service.get_students()