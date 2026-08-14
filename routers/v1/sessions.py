from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_user
from core.deps import (
    get_session_repository,
    get_session_service,
    get_task_service,
)
from repositories.session_repository import SessionRepository
from schemas.sessions import (
    EndSessionRequest,
    EndSessionResponse,
    PracticeSession,
    SetCurrentTaskRequest,
    StartSessionRequest,
    StartSessionResponse,
)
from services.session_service import SessionService
from services.task_service import TaskService

router = APIRouter(tags=["Sessions"])


@router.post(
    "/sessions/start",
    summary="Start practice",
    description="Start a practice session, optionally with an initial task.",
    response_model=PracticeSession,
)
async def start_practice(
    user: Annotated[dict, Depends(get_current_user)],
    body: StartSessionRequest | None = None,
    task_service: TaskService = Depends(get_task_service),
    session_service: SessionService = Depends(get_session_service),
):
    task = None
    if body and body.task_id is not None:
        task = task_service.get_task_by_id(body.task_id, user.id)
    return session_service.start_session(user=user, task=task)


@router.post(
    "/sessions/start/{task_id}",
    summary="Start session (legacy)",
    description="Compatibility endpoint for starting a session with a task.",
    response_model=StartSessionResponse,
)
async def start_session_legacy(
    task_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    task_service: TaskService = Depends(get_task_service),
    session_service: SessionService = Depends(get_session_service),
):
    task = task_service.get_task_by_id(task_id, user.id)
    return session_service.start_legacy_session(task, user)


@router.post(
    "/sessions/{session_id}/current-task",
    summary="Choose the current task",
    description="Add a task to the session and make it the current task.",
    response_model=PracticeSession,
)
async def set_current_task(
    session_id: int,
    body: SetCurrentTaskRequest,
    user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
):
    return session_service.set_current_task(
        session_id=session_id,
        task_id=body.task_id,
        user=user,
    )


@router.delete(
    "/sessions/{session_id}/current-task",
    summary="Clear the current task",
    description="Finish with the current task for now without ending the session.",
    response_model=PracticeSession,
)
async def clear_current_task(
    session_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
):
    return session_service.clear_current_task(session_id=session_id, user=user)


@router.post(
    "/sessions/{session_id}/end",
    summary="End practice",
    description="End a practice session without changing task completion status.",
    response_model=PracticeSession,
)
async def end_practice(
    session_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    body: EndSessionRequest | None = None,
    session_service: SessionService = Depends(get_session_service),
):
    return session_service.end_session(
        session_id=session_id,
        user=user,
        notes=body.notes if body else None,
    )


@router.post(
    "/sessions/end/{task_id}",
    summary="End a practice session (legacy)",
    description="Compatibility endpoint for the current task-based frontend.",
    response_model=EndSessionResponse,
)
async def end_session_legacy(
    task_id: int,
    body: EndSessionRequest,
    user: Annotated[dict, Depends(get_current_user)],
    session_service: SessionService = Depends(get_session_service),
    task_service: TaskService = Depends(get_task_service),
):
    task = task_service.get_task_by_id(task_id, user.id)
    return session_service.end_legacy_session(task, user, body.notes)


@router.get(
    "/sessions",
    summary="Get practice sessions",
    description="Get rich session history including all practised tasks.",
    response_model=list[PracticeSession],
)
async def get_sessions(
    user: Annotated[dict, Depends(get_current_user)],
    service: SessionService = Depends(get_session_service),
):
    return service.get_all_sessions(user)


@router.get(
    "/sessions/active",
    summary="Get active session",
    description="Get the current active practice session for the current user.",
    response_model=PracticeSession | None,
)
async def get_active_session(
    user: Annotated[dict, Depends(get_current_user)],
    service: SessionService = Depends(get_session_service),
):
    return service.get_active_session(user)


@router.get(
    "/sessions/{session_id}",
    summary="Get a practice session",
    response_model=PracticeSession,
)
async def get_session(
    session_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    session_repo: SessionRepository = Depends(get_session_repository),
):
    session = session_repo.get_session_by_id(session_id, user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_repo._to_response(session)


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
    service.delete_session(session_id, user)
