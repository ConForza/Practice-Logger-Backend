from datetime import datetime

from fastapi import HTTPException

from repositories.session_repository import SessionRepository
from repositories.task_repository import TaskRepository
from schemas.sessions import EndSessionResponse, PracticeSession, StartSessionResponse


class SessionService:
    def __init__(self, session_repo: SessionRepository, task_repo: TaskRepository):
        self.session_repo = session_repo
        self.task_repo = task_repo

    @staticmethod
    def calculate_session_duration(start_time: datetime) -> int:
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        return max(0, int(elapsed_seconds // 60))

    def _ensure_no_active_session(self, user):
        if self.session_repo.get_active_session(user) is not None:
            raise HTTPException(
                status_code=400,
                detail="Session is already in progress.",
            )

    def start_session(self, user, task=None) -> PracticeSession:
        if task is not None and task.status == "completed":
            raise HTTPException(
                status_code=400,
                detail="Cannot start a completed task.",
            )

        self._ensure_no_active_session(user)
        return self.session_repo.start_session(user=user, task=task)

    def start_legacy_session(self, task, user) -> StartSessionResponse:
        session = self.start_session(user=user, task=task)
        return StartSessionResponse(
            id=session.id,
            task_id=task.id,
            title=task.title,
            start_time=session.started_at,
            status="active",
        )

    def set_current_task(self, session_id: int, task_id: int, user):
        session = self.session_repo.get_session_by_id(session_id, user.id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.ended_at is not None:
            raise HTTPException(
                status_code=400,
                detail="Cannot change the task on a completed session.",
            )

        task = self.task_repo.get_task_by_id(task_id, user.id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status == "completed":
            raise HTTPException(
                status_code=400,
                detail="Cannot practise a completed task.",
            )

        return self.session_repo.set_current_task(session, task)

    def clear_current_task(self, session_id: int, user):
        session = self.session_repo.get_session_by_id(session_id, user.id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.ended_at is not None:
            raise HTTPException(
                status_code=400,
                detail="Cannot change the task on a completed session.",
            )
        return self.session_repo.clear_current_task(session)

    def end_session(
        self,
        session_id: int,
        user,
        notes: str | None = None,
        enforce_minimum_duration: bool = False,
    ) -> PracticeSession:
        session = self.session_repo.get_session_by_id(session_id, user.id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.ended_at is not None:
            raise HTTPException(status_code=400, detail="Session already ended")

        duration = self.calculate_session_duration(
            session.started_at or session.timestamp
        )
        if enforce_minimum_duration and duration < 1:
            raise HTTPException(
                status_code=400,
                detail="Practice session must last at least 1 minute.",
            )

        return self.session_repo.end_session(session, duration, notes)

    def end_legacy_session(self, task, user, notes: str | None = None):
        session = self.session_repo.get_session_by_task_id(task.id, user.id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        ended_session = self.end_session(
            session_id=session.id,
            user=user,
            notes=notes,
            enforce_minimum_duration=True,
        )
        # Preserve the old route's behaviour for the current frontend. The new
        # session endpoint deliberately does not complete the task.
        self.task_repo.update_task_status(task.id, user.id, "completed")
        return EndSessionResponse(
            id=ended_session.id,
            task_id=task.id,
            title=task.title,
            duration=ended_session.duration,
            start_time=ended_session.started_at,
            notes=ended_session.notes,
            status="completed",
        )

    def get_all_sessions(self, user):
        return self.session_repo.get_all_sessions(user)

    def get_active_session(self, user):
        return self.session_repo.get_active_session(user)

    def delete_session(self, session_id, user):
        deleted_session_id = self.session_repo.delete_session(session_id, user)
        if not deleted_session_id:
            raise HTTPException(status_code=404, detail="Session not found")
