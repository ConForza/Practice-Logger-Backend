from fastapi import HTTPException, status
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from schemas.tasks import TaskResponse


class TaskService:
    def __init__(self, task_repo: TaskRepository, user_repo: UserRepository):
        self.task_repo = task_repo
        self.user_repo = user_repo

    def get_all_tasks(self, user_id: int) -> list[TaskResponse]:
        tasks = self.task_repo.get_all_tasks(user_id)
        return tasks

    def update_task(self, task_id: int, user_id: int, body):
        task = self.task_repo.update_task(task_id, user_id, body)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def delete_task(self, task_id: int, user_id: int):
        try:
            deleted_task_id = self.task_repo.delete_task(task_id, user_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )

        if deleted_task_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return deleted_task_id

    def get_task_by_id(self, task_id: int, user_id: int):
        task = self.task_repo.get_task_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def create_task(self, body, user_id: int):
        return self.task_repo.create_task(body, user_id)