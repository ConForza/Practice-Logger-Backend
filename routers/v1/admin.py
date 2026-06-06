from fastapi import APIRouter, Depends

from core.auth import require_admin
from schemas.auth import UserResponse
from core.deps import get_admin_service
from services.admin_service import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/status")
async def admin_status(
    current_user: UserResponse = Depends(require_admin),
):
    return {
        "message": "Admin router is working",
        "user": current_user,
    }

@router.get("/users", response_model=list[UserResponse])
async def get_admin_users(
    current_user: UserResponse = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    return admin_service.get_users()