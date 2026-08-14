from typing import Annotated
from fastapi import APIRouter, Depends, status
from core.auth import get_current_user

from core.deps import get_task_service
from schemas.tasks import TaskRequest, TaskResponse, TaskStatusUpdateRequest
from services.task_service import TaskService

router = APIRouter(tags=["Tasks"])

@router.get(
    "/tasks",
    response_model=list[TaskResponse],
    summary="Get all tasks",
    description="Retrieves all tasks for the current user.",
    )
async def get_all_tasks(
    user: Annotated[dict, Depends(get_current_user)],
    service: TaskService = Depends(get_task_service)
):
    return service.get_all_tasks(user.id)

@router.post(
    "/tasks",
    response_model=TaskResponse,
    summary="Create a new task",
    description="Create a new task for the current user.",
    )
async def create_task(
    task: TaskRequest,
    user: Annotated[dict, Depends(get_current_user)],
    service: TaskService = Depends(get_task_service)
):
    return service.create_task(task, user.id)

@router.put(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update a task",
    description="Update a task by id number.",
    )
async def update_task(
    task_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    body: TaskRequest,
    service: TaskService = Depends(get_task_service)
):
    return service.update_task(task_id, user.id, body)


@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskResponse,
    summary="Update task status",
    description="Mark a task open or completed.",
)
async def update_task_status(
    task_id: int,
    body: TaskStatusUpdateRequest,
    user: Annotated[dict, Depends(get_current_user)],
    service: TaskService = Depends(get_task_service),
):
    return service.update_status(task_id, user.id, body.status)

@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Delete a task by id number.",
)
async def delete_task(
    task_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    service: TaskService = Depends(get_task_service)
):
    service.delete_task(task_id, user.id)
