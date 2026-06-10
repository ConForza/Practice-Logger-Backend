from fastapi import HTTPException, status

from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from repositories.task_repository import TaskRepository

class TeacherService:
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository, task_repo: TaskRepository):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.task_repo = task_repo

    def get_students(self):
        return self.user_repo.get_students()

    def get_student_sessions(self, student_id: int):
        student = self.user_repo.get_user_by_id(student_id)

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        if student.role != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested user is not a student",
            )

        if self.session_repo is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session repository not configured",
            )
        return self.session_repo.get_sessions_by_user_id(student_id)

    def assign_task_to_student(self, task_data, student_id: int):
        student = self.user_repo.get_user_by_id(student_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        if student.role != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested user is not a student",
            )

        return self.task_repo.create_task(task_data, student_id)

    def get_weekly_student_progress(self):
        return self.session_repo.get_weekly_student_progress()