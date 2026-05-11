from sqlalchemy.orm import Session
from db.models import SessionDB, TaskDB
from datetime import datetime

from schemas.sessions import StartSessionResponse, EndSessionResponse


class SessionRepository:

    def __init__(self, db: Session):
        self.db = db

    def start_session(self, task):
        db_session = SessionDB(
            task_id=task.id,
            timestamp=datetime.now(),
            duration=0,
        )

        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return StartSessionResponse(
            id=db_session.id,
            title=task.title,
            task_id=db_session.task_id,
            start_time=db_session.timestamp,
        )

    def get_session_by_task_id(self, task_id):
        session = self.db.query(SessionDB).filter(SessionDB.task_id == task_id).first()
        if session is None:
            return None
        return session

    def end_session(self, task, duration, notes: str | None = None):
        session, task = (
            self.db.query(SessionDB, TaskDB).join(TaskDB, SessionDB.task_id == TaskDB.id)
            .filter(SessionDB.task_id == task.id)
            .first()
        )

        session.duration = duration

        if notes:
            session.notes = notes

        self.db.commit()
        self.db.refresh(session)

        return EndSessionResponse(
            id=session.id,
            title=task.title,
            duration=session.duration,
            notes=session.notes,
            start_time=session.timestamp,
            task_id=session.task_id,
        )

    def get_active_session(self, user):
        result = (
            self.db.query(SessionDB, TaskDB)
            .join(TaskDB, SessionDB.task_id == TaskDB.id)
            .filter(TaskDB.user_id == user.id)
            .filter(TaskDB.status == "in progress")
            .order_by(SessionDB.timestamp.desc())
            .first()
        )

        if result is None:
            return None

        session, task = result

        return StartSessionResponse(
            id=session.id,
            task_id=session.task_id,
            title=task.title,
            start_time=session.timestamp,
            status="in progress",
            )

    def delete_session(self, session_id, user):
        query = self.db.query(SessionDB)
        session = (
            query.join(TaskDB, SessionDB.task_id == TaskDB.id)
            .filter(TaskDB.user_id == user.id)
            .filter(SessionDB.id == session_id)
            .first()
        )
        if session:
            self.db.delete(session)
            self.db.commit()
            return session.id
        return None

    def get_all_sessions(self, user):
        sessions = []
        query = self.db.query(SessionDB, TaskDB)
        rows = (
            query.join(TaskDB, SessionDB.task_id == TaskDB.id)
            .filter(TaskDB.user_id == user.id)
            .order_by(SessionDB.timestamp.desc())
            .all()
        )
        for session, task in rows:
            sessions.append(
                EndSessionResponse(
                    id=session.id,
                    title=task.title,
                    duration=session.duration,
                    notes=session.notes,
                    start_time=session.timestamp,
                    task_id=session.task_id,
                )
            )
        return sessions