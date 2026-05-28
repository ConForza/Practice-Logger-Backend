from fastapi import APIRouter, Depends

from core.auth import require_teacher, require_admin
from schemas.auth import UserResponse

router = APIRouter(tags=["Role Test"])

@router.get("/teacher/dashboard")
async def teacher_dashboard(
    current_user: UserResponse = Depends(require_teacher),
):
    return {
        "message": "Teacher dashboard access granted",
        "user": current_user,
    }

@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: UserResponse = Depends(require_admin),
):
    return {
        "message": "Admin dashboard access granted",
        "user": current_user,
    }