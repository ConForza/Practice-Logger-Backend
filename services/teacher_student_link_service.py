from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from repositories.teacher_student_link_repository import TeacherStudentLinkRepository
from repositories.user_repository import UserRepository


class TeacherStudentLinkService:
    def __init__(
        self,
        link_repo: TeacherStudentLinkRepository,
        user_repo: UserRepository,
    ):
        self.link_repo = link_repo
        self.user_repo = user_repo

    def get_all_links(self):
        return self.link_repo.get_all_links()

    def create_link(self, teacher_id: int, student_id: int, instrument: str):
        teacher = self.user_repo.get_user_by_id(teacher_id)

        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found",
            )

        if teacher.role != "teacher":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected teacher must have teacher role",
            )

        student = self.user_repo.get_user_by_id(student_id)

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        if student.role != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected student must have student role",
            )

        cleaned_instrument = instrument.strip()

        if not cleaned_instrument:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Instrument is required",
            )

        try:
            return self.link_repo.create_link(
                teacher_id=teacher_id,
                student_id=student_id,
                instrument=cleaned_instrument,
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This teacher-student-instrument link already exists",
            )

    def delete_link(self, link_id: int):
        deleted_link_id = self.link_repo.delete_link(link_id)

        if deleted_link_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher-student link not found",
            )

        return {"message": "Teacher-student link deleted successfully"}
