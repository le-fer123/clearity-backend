import json
import logging
from typing import List, Optional
from uuid import UUID

from app.database import db

logger = logging.getLogger(__name__)


class MessageRepository:
    async def create_message(self, session_id: UUID, role: str, content: str, metadata: dict = None) -> UUID:
        message_id = await db.fetchval(
            "INSERT INTO messages (session_id, role, content, metadata) VALUES ($1, $2, $3, $4) RETURNING id",
            session_id, role, content, json.dumps(metadata) if metadata else None
        )
        logger.info(f"Created message {message_id} in session {session_id}")
        return message_id

    async def get_session_messages(self, session_id: UUID, limit: int = 50) -> List[dict]:
        messages = await db.fetch(
            """SELECT id, session_id, role, content, metadata, created_at
               FROM messages
               WHERE session_id = $1
               ORDER BY created_at ASC
               LIMIT $2""",
            session_id, limit
        )
        return [dict(m) for m in messages]

    async def get_recent_messages(self, session_id: UUID, limit: int = 10) -> List[dict]:
        messages = await db.fetch(
            """SELECT id, session_id, role, content, metadata, created_at
               FROM messages
               WHERE session_id = $1
               ORDER BY created_at DESC
               LIMIT $2""",
            session_id, limit
        )
        return [dict(m) for m in reversed(messages)]


class SnapshotRepository:
    async def create_snapshot(
            self,
            session_id: UUID,
            mind_map_id: Optional[UUID],
            snapshot_data: dict,
            progress_notes: Optional[str] = None,
            unresolved_issues: List[str] = None
    ) -> UUID:
        snapshot_id = await db.fetchval(
            """INSERT INTO snapshots (session_id, mind_map_id, snapshot_data, progress_notes, unresolved_issues)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            session_id, mind_map_id, json.dumps(snapshot_data), progress_notes, json.dumps(unresolved_issues or [])
        )
        logger.info(f"Created snapshot {snapshot_id} for session {session_id}")
        return snapshot_id

    async def get_session_snapshots(self, session_id: UUID, limit: int = 5) -> List[dict]:
        snapshots = await db.fetch(
            """SELECT id, session_id, mind_map_id, snapshot_data, progress_notes, unresolved_issues, created_at
               FROM snapshots
               WHERE session_id = $1
               ORDER BY created_at DESC
               LIMIT $2""",
            session_id, limit
        )
        return [dict(s) for s in snapshots]

    async def get_latest_snapshot(self, session_id: UUID) -> Optional[dict]:
        snapshot = await db.fetchrow(
            """SELECT id, session_id, mind_map_id, snapshot_data, progress_notes, unresolved_issues, created_at
               FROM snapshots
               WHERE session_id = $1
               ORDER BY created_at DESC
               LIMIT 1""",
            session_id
        )
        return dict(snapshot) if snapshot else None

    async def find_similar_snapshots(self, user_id: UUID, keywords: List[str], limit: int = 3) -> List[dict]:
        snapshots = await db.fetch(
            """SELECT s.id, s.session_id, s.mind_map_id, s.snapshot_data, s.progress_notes,
                      s.unresolved_issues, s.created_at, m.map_name, m.central_theme
               FROM snapshots s
               JOIN sessions sess ON s.session_id = sess.id
               LEFT JOIN mind_maps m ON s.mind_map_id = m.id
               WHERE sess.user_id = $1
               ORDER BY s.created_at DESC
               LIMIT $2""",
            user_id, limit
        )
        return [dict(s) for s in snapshots]

    async def get_mind_map_snapshots(self, mind_map_id: UUID, limit: int = 5) -> List[dict]:
        snapshots = await db.fetch(
            """SELECT id, session_id, mind_map_id, snapshot_data, progress_notes, unresolved_issues,
                      created_at
               FROM snapshots
               WHERE mind_map_id = $1
               ORDER BY created_at DESC
               LIMIT $2""",
            mind_map_id, limit
        )
        return [dict(s) for s in snapshots]


message_repository = MessageRepository()
snapshot_repository = SnapshotRepository()
