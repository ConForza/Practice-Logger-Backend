from fastapi import HTTPException, status

from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from repositories.task_repository import TaskRepository
from repositories.teacher_student_link_repository import TeacherStudentLinkRepository


class TeacherService:
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository, task_repo: TaskRepository,
                 link_repo: TeacherStudentLinkRepository):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.task_repo = task_repo
        self.link_repo = link_repo

    def ensure_teacher_can_access_student(self, teacher_id: int, student_id: int):
        link = self.link_repo.get_link_for_teacher_and_student(teacher_id, student_id)

        if not link:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this student",
            )

        return link

    def get_students(self, teacher_id: int):
        return self.user_repo.get_students_for_teacher(teacher_id)

    def get_student_sessions(self, teacher_id, student_id: int):
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

        self.ensure_teacher_can_access_student(teacher_id, student_id)
        return self.session_repo.get_sessions_by_user_id(student_id)

    def assign_task_to_student(self, task_data, teacher_id: int, student_id: int):
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

        link = self.link_repo.get_link_for_teacher_and_student(teacher_id, student_id)
        self.ensure_teacher_can_access_student(teacher_id, student_id)
        return self.task_repo.create_task(task_data, student_id, link.id)

    def get_weekly_student_progress(self, teacher_id: int):
        return self.session_repo.get_weekly_student_progress(teacher_id)
