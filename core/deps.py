from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import SessionLocal
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository
from repositories.teacher_student_link_repository import TeacherStudentLinkRepository
from services.session_service import SessionService
from services.task_service import TaskService
from services.teacher_service import TeacherService
from services.user_service import UserService
from services.admin_service import AdminService
from services.teacher_student_link_service import TeacherStudentLinkService


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

def get_teacher_student_link_repository(db: Session = Depends(get_db)):
    return TeacherStudentLinkRepository(db)

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

def get_admin_service(
    user_repo: UserRepository = Depends(get_user_repository),
):
    return AdminService(user_repo)

def get_teacher_student_link_service(
    link_repo: TeacherStudentLinkRepository = Depends(get_teacher_student_link_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    return TeacherStudentLinkService(link_repo, user_repo)
