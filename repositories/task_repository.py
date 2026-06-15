from sqlalchemy.orm import Session
from db.models import TaskDB, SessionDB
from schemas.tasks import TaskResponse


class TaskRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all_tasks(self, user_id: int) -> list[TaskResponse]:
        tasks = []
        query = self.db.query(TaskDB)
        rows = query.filter(TaskDB.user_id == user_id).all()
        for row in rows:
            tasks.append(
                TaskResponse(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    status=row.status,
                    user_id=row.user_id,
                )
            )
        return tasks

    def update_task(self, task_id: int, user_id: int, task_request):
        row = (
            self.db.query(TaskDB)
            .filter(TaskDB.id == task_id)
            .filter(TaskDB.user_id == user_id)
            .first()
        )
        if row:
            row.title = task_request.title
            row.description = task_request.description

            self.db.commit()
            self.db.refresh(row)

            return TaskResponse(
                id=row.id,
                title=row.title,
                description=row.description,
                status=row.status,
                user_id=row.user_id,
            )
        return None

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
                .filter(SessionDB.task_id == task_id)
                .first()
                is not None
        )

        if has_sessions:
            raise ValueError("Cannot delete a task with practice sessions")

        self.db.delete(task)
        self.db.commit()

        return task_id

    def get_task_by_id(self, task_id: int, user_id: int):
        row = (
            self.db.query(TaskDB)
            .filter(TaskDB.id == task_id)
            .filter(TaskDB.user_id == user_id)
            .first()
        )
        if not row:
            return None
        return TaskResponse(
            id=row.id,
            title=row.title,
            description=row.description,
            status=row.status,
            user_id=row.user_id,
        )

    def create_task(self, body, user_id: int):
        db_task = TaskDB(
            title=body.title,
            description=body.description,
            status="pending",
            user_id=user_id,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)

        return TaskResponse(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            user_id=db_task.user_id,
        )

    def update_task_status(self, task_id: int, status: str):
        row = (
            self.db.query(TaskDB)
            .filter(TaskDB.id == task_id)
            .first()
        )

        row.status = status
        self.db.commit()
        self.db.refresh(row)