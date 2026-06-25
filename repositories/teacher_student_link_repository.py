from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.models import TeacherStudentLinkDB


class TeacherStudentLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_link(self, teacher_id: int, student_id: int, instrument: str):
        link = TeacherStudentLinkDB(
            teacher_id=teacher_id,
            student_id=student_id,
            instrument=instrument.strip(),
        )

        self.db.add(link)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise

        self.db.refresh(link)
        return link

    def get_all_links(self):
        return self.db.query(TeacherStudentLinkDB).order_by(
            TeacherStudentLinkDB.id.desc()
        ).all()

    def get_link_by_id(self, link_id: int):
        return (
            self.db.query(TeacherStudentLinkDB)
            .filter(TeacherStudentLinkDB.id == link_id)
            .first()
        )

    def delete_link(self, link_id: int):
        link = self.get_link_by_id(link_id)

        if not link:
            return None

        self.db.delete(link)
        self.db.commit()

        return link_id
