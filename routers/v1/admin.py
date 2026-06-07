from fastapi import APIRouter, Depends, HTTPException

from core.auth import require_admin
from schemas.auth import UserResponse, UserRoleUpdate, UserStatusUpdate
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
async def get_users(
    current_user: UserResponse = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    return admin_service.get_users()

@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: UserResponse = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    if user_id == current_user.id and role_data.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin role.",
        )

    return admin_service.update_user_role(user_id, role_data.role)

@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    current_user: UserResponse = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    if user_id == current_user.id and status_data.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account.",
        )

    return admin_service.update_user_status(user_id, status_data.is_active)