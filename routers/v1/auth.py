from fastapi import APIRouter, Depends, status
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm

from services.user_service import UserService
from core.deps import get_user_service
from core.auth import get_current_user, require_admin
from schemas.auth import UserResponse, CreateUserRequest, TokenResponse, UserLoginRequest, UserPasswordUpdate

router = APIRouter(tags=["Auth"])

@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates and stores a new user record.",
)
async def create_user(
    body: CreateUserRequest,
    service: UserService = Depends(get_user_service)
):
    return service.create_user(body)

@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="User login",
    description="Login a user with and email and password.",
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    body = UserLoginRequest(
        email=form_data.username,
        password=form_data.password,
    )
    return service.login_user(body)

@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the currently authenticated user.",
)
async def get_me(
    user: Annotated[dict, Depends(get_current_user)],
):
    return user

@router.patch("/users/{user_id}/password")
async def reset_user_password(
    user_id: int,
    password_data: UserPasswordUpdate,
    current_user: UserResponse = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.reset_user_password(
        user_id=user_id,
        new_password=password_data.new_password,
    )