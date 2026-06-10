from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from datetime import datetime, timedelta

from core.auth import get_current_user
from core.deps import get_task_service, get_session_service, get_session_repository
from repositories.session_repository import SessionRepository
from schemas.sessions import StartSessionResponse, EndSessionResponse, EndSessionRequest
from services.session_service import SessionService
from services.task_service import TaskService

router = APIRouter(tags=["Sessions"])

def calculate_streak(
    user: Annotated[dict, Depends(get_current_user)],
    session_repo: SessionRepository = Depends(get_session_repository),
):
    streak = 0
    date_to_compare = datetime.today()
    sessions = session_repo.get_all_sessions(user)
    for session in sessions:
        if session.start_time.date() == date_to_compare:
            streak += 1
        else:
            break

        date_to_compare = datetime.today() - timedelta(days=1)

    print(streak)


@router.post(
    "/sessions/start/{task_id}",
    summary="Start session",
    description="Start a practice session",
    response_model=StartSessionResponse,
)
async def start_session(
    task_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
    session_service: SessionService = Depends(get_session_service),
):
    task = task_service.get_task_by_id(task_id, user.id)
    return session_service.start_session(task, user)

@router.post(
    "/sessions/end/{task_id}",
    summary="End a practice session",
    description="Ends a practice session from a session id",
    response_model=EndSessionResponse,
)
async def end_session(
    task_id: int,
    body: EndSessionRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
    task_service: TaskService = Depends(get_task_service),
    session_repo: SessionRepository = Depends(get_session_repository),
):
    task = task_service.get_task_by_id(task_id, user.id)
    background_tasks.add_task(calculate_streak, user, session_repo)
    return session_service.end_session(task, body.notes)

@router.get(
    "/sessions",
    summary="Get all sessions",
    description="Get all practice sessions for the current user.",
    response_model=list[EndSessionResponse],
)
async def get_sessions(
    user: Annotated[dict, Depends(get_current_user)],
    service: SessionService = Depends(get_session_service),
):
    return service.get_all_sessions(user)

@router.get("/sessions/active",
    summary="Get active session",
    description="Get the current active practice session for the current user.",
    response_model=StartSessionResponse | None,
            )
async def get_active_session(
        user: Annotated[dict, Depends(get_current_user)],
        service: SessionService = Depends(get_session_service),
):
    return service.get_active_session(user)

@router.delete(
    "/sessions/{session_id}",
    summary="Delete a practice session",
    description="Deletes a practice session for the current user.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(
    session_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    service: SessionService = Depends(get_session_service),
):
    return service.delete_session(session_id, user)