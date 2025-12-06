import logging
from typing import Optional
from uuid import UUID

from app.database import db

logger = logging.getLogger(__name__)


class SessionRepository:
    async def create_session(self, user_id: Optional[UUID] = None) -> dict:
        if user_id is None:
            user_id = await db.fetchval("INSERT INTO users DEFAULT VALUES RETURNING id")
            logger.info(f"Created new user: {user_id}")

        session = await db.fetchrow(
            "INSERT INTO sessions (user_id) VALUES ($1) RETURNING id, user_id, created_at, updated_at",
            user_id
        )
        logger.info(f"Created session {session['id']} for user {user_id}")
        return dict(session)

    async def get_session(self, session_id: UUID) -> Optional[dict]:
        session = await db.fetchrow(
            "SELECT id, user_id, created_at, updated_at FROM sessions WHERE id = $1",
            session_id
        )
        return dict(session) if session else None

    async def update_session(self, session_id: UUID):
        await db.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = $1",
            session_id
        )

    async def get_user_sessions(self, user_id: UUID, limit: int = 10):
        sessions = await db.fetch(
            "SELECT id, user_id, created_at, updated_at FROM sessions WHERE user_id = $1 ORDER BY updated_at DESC LIMIT $2",
            user_id, limit
        )
        return [dict(s) for s in sessions]


session_repository = SessionRepository()
