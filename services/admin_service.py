from repositories.user_repository import UserRepository

class AdminService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_users(self):
        return self.user_repo.get_users()