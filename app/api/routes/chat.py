import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from starlette.requests import Request

from app.auth.dependencies import get_optional_user
from app.rate_limit import limiter
from app.models.requests import ChatMessageRequest
from app.models.responses import ChatResponse, MessageResponse
from app.repositories.session_repository import session_repository
from app.repositories.message_repository import message_repository
from app.services.layer1_orchestrator import layer1_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("5/minute")
async def send_message(
        request: Request,
        body: ChatMessageRequest,
        current_user_id: Optional[UUID] = Depends(get_optional_user)
):
    logger.info(f"Received chat message (authenticated: {current_user_id is not None})")

    # Authenticated user
    if current_user_id:
        user_id = current_user_id
        logger.info(f"Authenticated user: {user_id}")
    # Anonymous - backward compatibility with user_id in request
    elif body.user_id:
        user_id = body.user_id
        logger.info(f"Anonymous user (from request): {user_id}")
    # Create new anonymous user
    else:
        user_id = await session_repository.create_anonymous_user()
        logger.info(f"Created anonymous user: {user_id}")

    # Handle session
    if body.session_id is None:
        session = await session_repository.create_session(user_id)
        session_id = session["id"]
        logger.info(f"Created new session {session_id}")
    else:
        session_id = body.session_id
        session = await session_repository.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify session belongs to user (only for authenticated)
        if current_user_id and session["user_id"] != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="Session does not belong to authenticated user"
            )

        user_id = session["user_id"]

    # Process message
    response = await layer1_orchestrator.process_message(
        session_id=session_id,
        user_id=user_id,
        message=body.message
    )

    logger.debug(f"Response for session {session_id}: {response.get('message', '')[:100]}...")
    logger.info(f"Chat message processed for session {session_id}")
    return ChatResponse(**response)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
@limiter.limit("20/minute")
async def get_session_messages(
        request: Request,
        session_id: UUID,
        limit: int = 50,
        current_user_id: Optional[UUID] = Depends(get_optional_user)
):
    """
    Get message history for a session.
    """
    # Verify session exists
    session = await session_repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify access rights
    if session["user_id"] != current_user_id:
        if current_user_id and session["user_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        pass

    messages = await message_repository.get_session_messages(session_id, limit=limit)
    return messages
