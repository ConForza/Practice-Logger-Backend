from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from db.models import (
    SessionDB,
    SessionTaskDB,
    TaskDB,
    TeacherStudentLinkDB,
    UserDB,
)
from schemas.sessions import PracticeSession, SessionTask
from schemas.teacher import WeeklyStudentProgress


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_week_start(self):
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    def _tasks_for_session(self, session_id: int) -> list[TaskDB]:
        return (
            self.db.query(TaskDB)
            .join(SessionTaskDB, SessionTaskDB.task_id == TaskDB.id)
            .filter(SessionTaskDB.session_id == session_id)
            .order_by(SessionTaskDB.id.asc())
            .all()
        )

    def _to_response(self, session: SessionDB) -> PracticeSession:
        tasks = self._tasks_for_session(session.id)
        task_by_id = {task.id: task for task in tasks}
        current_task = task_by_id.get(session.current_task_id)
        compatibility_task = current_task or task_by_id.get(session.task_id)
        if compatibility_task is None and tasks:
            compatibility_task = tasks[0]

        started_at = session.started_at or session.timestamp
        return PracticeSession(
            id=session.id,
            user_id=session.user_id or 0,
            started_at=started_at,
            ended_at=session.ended_at,
            duration=session.duration,
            notes=session.notes,
            current_task_id=session.current_task_id,
            tasks=[
                SessionTask(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=task.status,
                )
                for task in tasks
            ],
            status="active" if session.ended_at is None else "completed",
            start_time=started_at,
            task_id=compatibility_task.id if compatibility_task else None,
            title=compatibility_task.title if compatibility_task else None,
        )

    def start_session(self, user, task=None) -> PracticeSession:
        now = datetime.now()
        db_session = SessionDB(
            user_id=user.id,
            timestamp=now,
            started_at=now,
            duration=0,
            task_id=task.id if task else None,
            current_task_id=task.id if task else None,
        )
        self.db.add(db_session)
        self.db.flush()

        if task:
            self.db.add(
                SessionTaskDB(
                    session_id=db_session.id,
                    task_id=task.id,
                )
            )

        self.db.commit()
        self.db.refresh(db_session)
        return self._to_response(db_session)

    def get_session_by_id(self, session_id: int, user_id: int):
        return (
            self.db.query(SessionDB)
            .filter(SessionDB.id == session_id, SessionDB.user_id == user_id)
            .first()
        )

    def get_session_by_task_id(self, task_id: int, user_id: int):
        return (
            self.db.query(SessionDB)
            .filter(
                SessionDB.user_id == user_id,
                or_(
                    SessionDB.task_id == task_id,
                    SessionDB.current_task_id == task_id,
                ),
                SessionDB.ended_at.is_(None),
            )
            .order_by(SessionDB.started_at.desc(), SessionDB.timestamp.desc())
            .first()
        )

    def get_active_session(self, user) -> PracticeSession | None:
        session = (
            self.db.query(SessionDB)
            .filter(
                SessionDB.user_id == user.id,
                SessionDB.ended_at.is_(None),
            )
            .order_by(SessionDB.started_at.desc(), SessionDB.timestamp.desc())
            .first()
        )
        return self._to_response(session) if session else None

    def set_current_task(self, session: SessionDB, task):
        existing_link = (
            self.db.query(SessionTaskDB)
            .filter(
                SessionTaskDB.session_id == session.id,
                SessionTaskDB.task_id == task.id,
            )
            .first()
        )
        if existing_link is None:
            self.db.add(
                SessionTaskDB(session_id=session.id, task_id=task.id)
            )

        session.current_task_id = task.id
        if session.task_id is None:
            session.task_id = task.id

        self.db.commit()
        self.db.refresh(session)
        return self._to_response(session)

    def clear_current_task(self, session: SessionDB):
        session.current_task_id = None
        self.db.commit()
        self.db.refresh(session)
        return self._to_response(session)

    def end_session(
        self,
        session: SessionDB,
        duration: int,
        notes: str | None = None,
    ) -> PracticeSession:
        session.duration = duration
        session.ended_at = datetime.now()
        session.current_task_id = None
        if notes is not None:
            session.notes = notes

        self.db.commit()
        self.db.refresh(session)
        return self._to_response(session)

    def delete_session(self, session_id: int, user):
        session = self.get_session_by_id(session_id, user.id)
        if not session:
            return None

        self.db.query(SessionTaskDB).filter(
            SessionTaskDB.session_id == session.id
        ).delete(synchronize_session=False)
        self.db.delete(session)
        self.db.commit()
        return session.id

    def get_all_sessions(self, user, limit: int = 10):
        sessions = (
            self.db.query(SessionDB)
            .filter(SessionDB.user_id == user.id)
            .order_by(
                SessionDB.started_at.desc(),
                SessionDB.timestamp.desc(),
            )
            .limit(limit)
            .all()
        )
        return [self._to_response(session) for session in sessions]

    def get_sessions_by_user_id(self, user_id: int):
        sessions = (
            self.db.query(SessionDB)
            .filter(SessionDB.user_id == user_id)
            .order_by(
                SessionDB.started_at.desc(),
                SessionDB.timestamp.desc(),
            )
            .all()
        )
        return [self._to_response(session) for session in sessions]

    def get_weekly_student_progress(self, teacher_id: int):
        week_start = self.get_week_start()
        assigned_student_ids = (
            select(TeacherStudentLinkDB.student_id)
            .filter(TeacherStudentLinkDB.teacher_id == teacher_id)
            .distinct()
        )
        session_start = func.coalesce(SessionDB.started_at, SessionDB.timestamp)

        rows = (
            self.db.query(
                UserDB.id.label("student_id"),
                UserDB.email.label("email"),
                func.coalesce(func.sum(SessionDB.duration), 0).label(
                    "total_duration"
                ),
                func.count(SessionDB.id).label("session_count"),
            )
            .outerjoin(
                SessionDB,
                (SessionDB.user_id == UserDB.id)
                & (session_start >= week_start),
            )
            .filter(UserDB.id.in_(assigned_student_ids))
            .filter(UserDB.role == "student")
            .filter(UserDB.is_active == True)
            .group_by(UserDB.id, UserDB.email)
            .order_by(
                func.coalesce(func.sum(SessionDB.duration), 0).desc(),
                UserDB.email.asc(),
            )
            .all()
        )

        return [
            WeeklyStudentProgress(
                student_id=row.student_id,
                email=row.email,
                total_duration=row.total_duration,
                session_count=row.session_count,
            )
            for row in rows
        ]
