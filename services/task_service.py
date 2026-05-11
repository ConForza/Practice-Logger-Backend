from fastapi import HTTPException, status
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from schemas.tasks import TaskResponse


class TaskService:
    def __init__(self, task_repo: TaskRepository, user_repo: UserRepository):
        self.task_repo = task_repo
        self.user_repo = user_repo

    def get_all_tasks(self, user) -> list[TaskResponse]:
        tasks = self.task_repo.get_all_tasks(user)
        return tasks

    def update_task(self, task_id, user, body):
        task = self.task_repo.update_task(task_id, user, body)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def delete_task(self, task_id, user):
        task_id = self.task_repo.delete_task(task_id, user)
        if not task_id:
            raise HTTPException(status_code=404, detail="Task not found")

    def get_task_by_id(self, task_id, user):
        task = self.task_repo.get_task_by_id(task_id, user)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def create_task(self, body, user):
        return self.task_repo.create_task(body, user)