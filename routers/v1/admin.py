from fastapi import APIRouter, Depends

from core.auth import require_admin
from schemas.auth import UserResponse

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