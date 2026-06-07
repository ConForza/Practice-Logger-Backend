from fastapi import HTTPException, status

from repositories.user_repository import UserRepository

class AdminService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_users(self):
        return self.user_repo.get_users()

    def update_user_role(self, user_id: int, role: str):
        user = self.user_repo.update_user_role(user_id, role)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    def update_user_status(self, user_id: int, is_active: bool):
        user = self.user_repo.update_user_status(user_id, is_active)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user