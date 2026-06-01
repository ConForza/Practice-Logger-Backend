from fastapi import APIRouter, Depends

from core.auth import require_teacher
from schemas.auth import UserResponse

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