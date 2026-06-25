from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import require_admin
from schemas.auth import UserResponse, UserRoleUpdate, UserStatusUpdate
from schemas.teacher_student_links import TeacherStudentLinkCreate, TeacherStudentLinkResponse
from core.deps import get_admin_service, get_teacher_student_link_service
from services.admin_service import AdminService
from services.teacher_student_link_service import TeacherStudentLinkService

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

@router.get(
    "/teacher-student-links",
    response_model=list[TeacherStudentLinkResponse],
)
async def get_teacher_student_links(
    current_user: UserResponse = Depends(require_admin),
    link_service: TeacherStudentLinkService = Depends(
        get_teacher_student_link_service
    ),
):
    return link_service.get_all_links()


@router.post(
    "/teacher-student-links",
    response_model=TeacherStudentLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_teacher_student_link(
    link_data: TeacherStudentLinkCreate,
    current_user: UserResponse = Depends(require_admin),
    link_service: TeacherStudentLinkService = Depends(
        get_teacher_student_link_service
    ),
):
    return link_service.create_link(
        teacher_id=link_data.teacher_id,
        student_id=link_data.student_id,
        instrument=link_data.instrument,
    )


@router.delete("/teacher-student-links/{link_id}")
async def delete_teacher_student_link(
    link_id: int,
    current_user: UserResponse = Depends(require_admin),
    link_service: TeacherStudentLinkService = Depends(
        get_teacher_student_link_service
    ),
):
    return link_service.delete_link(link_id)