import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from app.rate_limit import limiter
from app.models.requests import CreateSessionRequest
from app.models.responses import SessionResponse, SnapshotCandidate
from app.repositories.session_repository import session_repository
from app.services.layer5_memory import layer5_memory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
@limiter.limit("5/minute")
async def create_session(request: Request, body: CreateSessionRequest):
    """
    Create a new session for a user.
    """
    try:
        session = await session_repository.create_session(body.user_id)
        logger.info(f"Created session {session['id']}")

        return SessionResponse(
            session_id=session["id"],
            user_id=session["user_id"],
            created_at=session["created_at"],
            updated_at=session["updated_at"]
        )

    except Exception as e:
        logger.error(f"Error creating session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
@limiter.limit("5/minute")
async def get_session(request: Request, session_id: UUID):
    """
    Get session information.
    """
    try:
        session = await session_repository.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            session_id=session["id"],
            user_id=session["user_id"],
            created_at=session["created_at"],
            updated_at=session["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")


@router.get("/users/{user_id}/snapshots", response_model=list[SnapshotCandidate])
@limiter.limit("5/minute")
async def get_user_snapshots(request: Request, user_id: UUID, limit: int = 3):
    """
    Get recent snapshot candidates for a user (for continuing previous sessions).
    """
    try:
        candidates = await layer5_memory.retrieve_snapshot_candidates(
            user_id=user_id,
            limit=limit
        )

        return [
            SnapshotCandidate(
                map_id=c["map_id"],
                map_name=c["map_name"],
                last_updated=c["last_updated"],
                summary=c["summary"],
                unresolved_issues=c["unresolved_issues"]
            )
            for c in candidates if c["map_id"]
        ]

    except Exception as e:
        logger.error(f"Error getting user snapshots: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting snapshots: {str(e)}")
