from fastapi import HTTPException
from repositories.session_repository import SessionRepository
from datetime import datetime

from repositories.task_repository import TaskRepository


class SessionService:
    def __init__(self, session_repo: SessionRepository, task_repo: TaskRepository):
        self.session_repo = session_repo
        self.task_repo = task_repo

    def calculate_session_duration(self, start_time):
        end_time = datetime.now()
        return int((end_time - start_time).total_seconds() // 60)

    def start_session(self, task, user):
        if task.status == "completed":
            raise HTTPException(status_code=400, detail="Cannot start a completed task.")

        if task.status == "in progress":
            raise HTTPException(status_code=400, detail="Session already started for this task.")

        if self.session_repo.get_active_session(user) is not None:
            raise HTTPException(status_code=400, detail="Session is already in progress.")

        self.task_repo.update_task_status(task.id, status="in progress")
        return self.session_repo.start_session(task)

    def end_session(self, task, notes: str | None = None):
        if task.status == "completed":
            raise HTTPException(status_code=400, detail="Task already completed")

        session = self.session_repo.get_session_by_task_id(task.id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        duration = self.calculate_session_duration(session.timestamp)

        if duration < 1:
            raise HTTPException(
                status_code=400,
                detail="Practice session must last at least 1 minute.",
            )

        self.task_repo.update_task_status(task.id, status="completed")

        return self.session_repo.end_session(task, duration, notes)

    def get_session_by_task_id(self, session_id):
        return self.session_repo.get_session_by_task_id(session_id)

    def get_all_sessions(self, user):
        sessions = self.session_repo.get_all_sessions(user)
        return sessions

    def get_active_session(self, user):
        return self.session_repo.get_active_session(user)

    def delete_session(self, session_id, user):
        session_id = self.session_repo.delete_session(session_id, user)
        if not session_id:
            raise HTTPException(status_code=404, detail="Session not found")
