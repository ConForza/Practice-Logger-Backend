from sqlalchemy.orm import Session
from db.models import UserDB
from schemas.auth import User, UserResponse, UserDBResponse


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str):
        row = (
            self.db.query(UserDB)
            .filter(UserDB.email == email)
            .first()
        )
        if row is None:
            return None

        return UserDBResponse(
            id=row.id,
            email=row.email,
            password=row.hashed_password,
            is_active=row.is_active,
            role=row.role,
        )

    def create_user(self, user: User):
        db_user = UserDB(
            email=user.email,
            hashed_password=user.password,
            is_active=user.is_active,
            role="student",
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            is_active=db_user.is_active,
            role=db_user.role,
        )

    def get_students(self):
        return (
            self.db.query(UserDB)
            .filter(UserDB.role == "student")
            .order_by(UserDB.email)
            .all()
        )

    def get_user_by_id(self, user_id: int):
        return self.db.query(UserDB).filter(UserDB.id == user_id).first()

    def get_users(self):
        return (
            self.db.query(UserDB)
            .order_by(UserDB.email)
            .all()
        )

    def update_user_role(self, user_id: int, role: str):
        user = self.get_user_by_id(user_id)

        if user is None:
            return None

        user.role = role

        self.db.commit()
        self.db.refresh(user)

        return user

    def update_user_status(self, user_id: int, is_active: bool):
        user = self.get_user_by_id(user_id)

        if user is None:
            return None

        user.is_active = is_active

        self.db.commit()
        self.db.refresh(user)

        return user