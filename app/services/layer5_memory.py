import json
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.repositories.message_repository import snapshot_repository
from app.repositories.mindmap_repository import mindmap_repository

logger = logging.getLogger(__name__)


def parse_json_field(value):
    """Helper to parse JSON fields from database"""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return value
    return value


class Layer5Memory:
    """
    Layer 5 - Memory & Retrieval / Long-Term Brain

    Stores and retrieves snapshots of mind maps, issues, root causes, and tasks.
    Never talks to the user - only handles data persistence and retrieval.
    """

    async def store_snapshot(
            self,
            session_id: UUID,
            mind_map_id: Optional[UUID],
            snapshot_data: Dict[str, Any],
            progress_notes: Optional[str] = None,
            unresolved_issues: List[str] = None
    ) -> UUID:
        logger.info(f"Storing snapshot for session {session_id}")

        snapshot_id = await snapshot_repository.create_snapshot(
            session_id=session_id,
            mind_map_id=mind_map_id,
            snapshot_data=snapshot_data,
            progress_notes=progress_notes,
            unresolved_issues=unresolved_issues
        )

        logger.info(f"Snapshot {snapshot_id} stored successfully")
        return snapshot_id

    async def retrieve_latest_snapshot(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        logger.info(f"Retrieving latest snapshot for session {session_id}")

        snapshot = await snapshot_repository.get_latest_snapshot(session_id)

        if snapshot:
            logger.info(f"Found snapshot {snapshot['id']} from {snapshot['created_at']}")
            return {
                "snapshot_id": snapshot["id"],
                "mind_map_id": snapshot["mind_map_id"],
                "snapshot_data": parse_json_field(snapshot["snapshot_data"]),
                "progress_notes": snapshot["progress_notes"],
                "unresolved_issues": parse_json_field(snapshot["unresolved_issues"]),
                "created_at": snapshot["created_at"]
            }

        logger.info("No previous snapshot found")
        return None

    async def retrieve_snapshot_candidates(
            self,
            user_id: UUID,
            keywords: List[str] = None,
            limit: int = 3
    ) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving snapshot candidates for user {user_id}")

        snapshots = await snapshot_repository.find_similar_snapshots(
            user_id=user_id,
            keywords=keywords or [],
            limit=limit
        )

        candidates = []
        for snapshot in snapshots:
            snapshot_data = parse_json_field(snapshot.get("snapshot_data"))
            unresolved_issues = parse_json_field(snapshot.get("unresolved_issues"))

            candidates.append({
                "map_id": snapshot["mind_map_id"],
                "map_name": snapshot.get("map_name", "Unnamed Map"),
                "last_updated": snapshot["created_at"],
                "summary": snapshot_data.get("central_theme", "") if isinstance(snapshot_data, dict) else "",
                "unresolved_issues": unresolved_issues if isinstance(unresolved_issues, list) else []
            })

        logger.info(f"Found {len(candidates)} snapshot candidates")
        return candidates

    async def get_mind_map_state(self, mind_map_id: UUID) -> Optional[Dict[str, Any]]:
        logger.info(f"Retrieving full mind map state for {mind_map_id}")

        mind_map = await mindmap_repository.get_mind_map(mind_map_id)

        if mind_map:
            return {
                "mind_map_id": mind_map["id"],
                "map_name": mind_map["map_name"],
                "central_theme": mind_map["central_theme"],
                "created_at": mind_map["created_at"],
                "updated_at": mind_map["updated_at"]
            }

        return None

    async def should_continue_session(self, session_id: UUID) -> bool:
        snapshot = await self.retrieve_latest_snapshot(session_id)
        return snapshot is not None

    async def get_mind_map_snapshots(self, mind_map_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
        """Get all snapshots for a specific mind map"""
        logger.info(f"Retrieving snapshots for mind map {mind_map_id}")

        snapshots = await snapshot_repository.get_mind_map_snapshots(mind_map_id, limit=limit)

        results = []
        for snapshot in snapshots:
            results.append({
                "id": snapshot["id"],
                "mind_map_id": snapshot["mind_map_id"],
                "snapshot_data": parse_json_field(snapshot["snapshot_data"]),
                "progress_notes": snapshot.get("progress_notes"),
                "unresolved_issues": parse_json_field(snapshot["unresolved_issues"]),
                "created_at": snapshot.get("created_at"),
                "last_updated": snapshot.get("created_at")  # Use created_at as last_updated
            })

        logger.info(f"Found {len(results)} snapshots")
        return results


layer5_memory = Layer5Memory()
