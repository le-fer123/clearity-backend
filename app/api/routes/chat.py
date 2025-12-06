import logging

from fastapi import APIRouter, HTTPException

from app.models.requests import ChatMessageRequest
from app.models.responses import ChatResponse
from app.repositories.session_repository import session_repository
from app.services.layer1_orchestrator import layer1_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatMessageRequest):
    """
    Main chat endpoint. Processes user message through all 5 layers.
    """
    try:
        logger.info(f"Received chat message for session {request.session_id}")

        if request.session_id is None:
            session = await session_repository.create_session(request.user_id)
            session_id = session["id"]
            user_id = session["user_id"]
            logger.info(f"Created new session {session_id}")
        else:
            session_id = request.session_id
            session = await session_repository.get_session(session_id)

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            user_id = session["user_id"]

        response = await layer1_orchestrator.process_message(
            session_id=session_id,
            user_id=user_id,
            message=request.message
        )

        logger.info(f"Received chat message for session {session_id}:\n\n{response}")
        logger.info(f"Chat message processed successfully for session {session_id}")
        return ChatResponse(**response)

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
