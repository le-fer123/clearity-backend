import logging
from typing import Optional
from uuid import UUID

from app.database import db

logger = logging.getLogger(__name__)


class MindMapRepository:
    async def create_mind_map(self, session_id: UUID, map_name: str, central_theme: str) -> UUID:
        mind_map_id = await db.fetchval(
            "INSERT INTO mind_maps (session_id, map_name, central_theme) VALUES ($1, $2, $3) RETURNING id",
            session_id, map_name, central_theme
        )
        logger.info(f"Created mind map {mind_map_id} for session {session_id}")
        return mind_map_id

    async def get_mind_map(self, mind_map_id: UUID) -> Optional[dict]:
        mind_map = await db.fetchrow(
            "SELECT id, session_id, map_name, central_theme, created_at, updated_at FROM mind_maps WHERE id = $1",
            mind_map_id
        )
        return dict(mind_map) if mind_map else None

    async def get_session_mind_map(self, session_id: UUID) -> Optional[dict]:
        mind_map = await db.fetchrow(
            "SELECT id, session_id, map_name, central_theme, created_at, updated_at FROM mind_maps WHERE session_id = $1 ORDER BY updated_at DESC LIMIT 1",
            session_id
        )
        return dict(mind_map) if mind_map else None

    async def update_mind_map(self, mind_map_id: UUID, map_name: str = None, central_theme: str = None):
        updates = []
        params = []
        param_count = 1

        if map_name:
            updates.append(f"map_name = ${param_count}")
            params.append(map_name)
            param_count += 1

        if central_theme:
            updates.append(f"central_theme = ${param_count}")
            params.append(central_theme)
            param_count += 1

        if updates:
            params.append(mind_map_id)
            query = f"UPDATE mind_maps SET {', '.join(updates)} WHERE id = ${param_count}"
            await db.execute(query, *params)
            logger.info(f"Updated mind map {mind_map_id}")


mindmap_repository = MindMapRepository()
