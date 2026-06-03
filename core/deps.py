from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import SessionLocal
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository
from services.session_service import SessionService
from services.task_service import TaskService
from services.teacher_service import TeacherService
from services.user_service import UserService


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_task_repository(db: Session = Depends(get_db)):
    return TaskRepository(db)

def get_user_repository(db: Session = Depends(get_db)):
    return UserRepository(db)

def get_session_repository(db: Session = Depends(get_db)):
    return SessionRepository(db)

def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    return TaskService(task_repo, user_repo)

def get_user_service(user_repo: UserRepository = Depends(get_user_repository)):
    return UserService(user_repo)

def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    return SessionService(session_repo, task_repo)

def get_teacher_service(
    user_repo: UserRepository = Depends(get_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    return TeacherService(user_repo, session_repo, task_repo)