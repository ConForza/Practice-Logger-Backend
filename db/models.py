from db.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DATETIME, ForeignKey

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

class SessionDB(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    duration = Column(Integer, nullable=False)
    notes = Column(String)
    timestamp = Column(DATETIME, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)