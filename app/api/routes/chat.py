import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from app.auth.dependencies import get_optional_user
from app.models.requests import ChatMessageRequest
from app.models.responses import ChatResponse
from app.repositories.session_repository import session_repository
from app.services.layer1_orchestrator import layer1_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user_id: Optional[UUID] = Depends(get_optional_user)
):
    """
    Main chat endpoint. Processes user message through all 5 layers.
    
    Anonymous mode: Don't send JWT token, just use session_id
    Authenticated mode: Send JWT token in Authorization header
    """
    try:
        logger.info(f"Received chat message (authenticated: {current_user_id is not None})")

        # Authenticated user
        if current_user_id:
            user_id = current_user_id
            logger.info(f"Authenticated user: {user_id}")
        # Anonymous - backward compatibility with user_id in request
        elif request.user_id:
            user_id = request.user_id
            logger.info(f"Anonymous user (from request): {user_id}")
        # Create new anonymous user
        else:
            user_id = await session_repository.create_anonymous_user()
            logger.info(f"Created anonymous user: {user_id}")

        # Handle session
        if request.session_id is None:
            session = await session_repository.create_session(user_id)
            session_id = session["id"]
            logger.info(f"Created new session {session_id}")
        else:
            session_id = request.session_id
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
            message=request.message
        )

        logger.debug(f"Response for session {session_id}: {response.get('message', '')[:100]}...")
        logger.info(f"Chat message processed for session {session_id}")
        return ChatResponse(**response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
