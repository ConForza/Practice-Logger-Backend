from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from db.models import SessionDB, SessionTaskDB, TaskDB
from schemas.tasks import TaskResponse


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_response(row: TaskDB) -> TaskResponse:
        return TaskResponse(
            id=row.id,
            title=row.title,
            description=row.description,
            status=row.status,
            user_id=row.user_id,
            teacher_student_link_id=row.teacher_student_link_id,
            completed_at=row.completed_at,
        )

    def get_all_tasks(self, user_id: int, limit: int = 10) -> list[TaskResponse]:
        rows = (
            self.db.query(TaskDB)
            .filter(TaskDB.user_id == user_id)
            .order_by(TaskDB.id.desc())
            .limit(limit)
            .all()
        )
        return [self._to_response(row) for row in rows]

    def update_task(self, task_id: int, user_id: int, task_request):
        row = (
            self.db.query(TaskDB)
            .filter(TaskDB.id == task_id, TaskDB.user_id == user_id)
            .first()
        )
        if not row:
            return None

        row.title = task_request.title
        row.description = task_request.description
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def delete_task(self, task_id: int, user_id: int):
        task = (
            self.db.query(TaskDB)
            .filter(TaskDB.id == task_id, TaskDB.user_id == user_id)
            .first()
        )

        if not task:
            return None

        has_sessions = (
            self.db.query(SessionDB)
            .filter(
                (SessionDB.task_id == task_id)
                | (SessionDB.current_task_id == task_id)
            )
            .first()
            is not None
        )
        has_joined_sessions = (
            self.db.query(SessionTaskDB)
            .filter(SessionTaskDB.task_id == task_id)
            .first()
            is not None
        )
        if has_sessions or has_joined_sessions:
            raise ValueError("Cannot delete a task with practice sessions")

        self.db.delete(task)
        self.db.commit()
        return task_id

    def get_task_by_id(self, task_id: int, user_id: int):
        row = (
            self.db.query(TaskDB)
            .filter(TaskDB.id == task_id, TaskDB.user_id == user_id)
            .first()
        )
        return self._to_response(row) if row else None

    def create_task(
        self,
        body,
        user_id: int,
        teacher_student_link_id: int | None = None,
    ):
        db_task = TaskDB(
            title=body.title,
            description=body.description,
            status="open",
            completed_at=None,
            user_id=user_id,
            teacher_student_link_id=teacher_student_link_id,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return self._to_response(db_task)

    def update_task_status(self, task_id: int, user_id: int, status: str):
        row = (
            self.db.query(TaskDB)
            .filter(TaskDB.id == task_id, TaskDB.user_id == user_id)
            .first()
        )
        if not row:
            return None

        row.status = status
        row.completed_at = datetime.now() if status == "completed" else None

        if status == "completed":
            self.db.execute(
                update(SessionDB)
                .where(
                    SessionDB.current_task_id == task_id,
                    SessionDB.ended_at.is_(None),
                )
                .values(current_task_id=None)
            )

        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)
