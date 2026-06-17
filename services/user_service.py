from fastapi import HTTPException, status

from core.jwt import create_access_token
from repositories.user_repository import UserRepository
from schemas.auth import CreateUserRequest, User, UserLoginRequest
from core.security import hash_password, verify_password


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, body: CreateUserRequest):
        email = body.email.lower().strip()
        if self.user_repo.get_user_by_email(email) is not None:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=email,
            password=hash_password(body.password),
            is_active=True,
            role="student",
        )

        user_response = self.user_repo.create_user(user)

        return user_response

    def login_user(self, body: UserLoginRequest):

        user = self.user_repo.get_user_by_email(body.email.lower().strip())

        if user is None or not verify_password(body.password, user.password):
            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,

                detail="Incorrect email or password",

            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Account is inactive",
            )

        token = create_access_token(
            data={
                "sub": user.email,
                "is_active": user.is_active,
                "user_id": user.id,
                "role": user.role,
            }
        )
        return {
            "access_token": token,
            "token_type": "bearer",
        }

    def reset_user_password(self, user_id: int, new_password: str):
        hashed_password = hash_password(new_password)

        updated_user = self.user_repo.update_user_password(
            user_id=user_id,
            hashed_password=hashed_password,
        )

        if updated_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {"message": "Password updated successfully"}

