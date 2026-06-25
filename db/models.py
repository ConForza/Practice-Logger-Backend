from db.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String, default="student", nullable=False)

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    teacher_student_link_id = Column(
        Integer,
        ForeignKey("teacher_student_links.id"),
        nullable=True,
    )

class SessionDB(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    duration = Column(Integer, nullable=False)
    notes = Column(String)
    timestamp = Column(DateTime, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)

class TeacherStudentLinkDB(Base):
    __tablename__ = "teacher_student_links"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "student_id",
            "instrument",
            name="unique_teacher_student_instrument_link",
        ),
    )