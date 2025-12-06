import logging
from typing import List, Optional
from uuid import UUID

from app.database import db

logger = logging.getLogger(__name__)


class ProjectRepository:
    async def create_project(
            self,
            mind_map_id: UUID,
            label: str,
            fields: List[str],
            emotion: str = "grey",
            parent_id: Optional[UUID] = None,
            clarity: Optional[str] = None,
            issue_severity: str = "none",
            importance_score: float = 0.5,
            is_core_issue: bool = False,
            is_visible: bool = True
    ) -> UUID:
        project_id = await db.fetchval(
            """INSERT INTO projects (mind_map_id, parent_id, label, emotion, clarity, issue_severity,
               importance_score, is_core_issue, is_visible)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id""",
            mind_map_id, parent_id, label, emotion, clarity, issue_severity,
            importance_score, is_core_issue, is_visible
        )

        for field_id in fields:
            await db.execute(
                "INSERT INTO project_fields (project_id, field_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                project_id, field_id
            )

        logger.info(f"Created project {project_id}: {label}")
        return project_id

    async def get_project(self, project_id: UUID) -> Optional[dict]:
        project = await db.fetchrow(
            """SELECT p.*, array_agg(pf.field_id) as fields
               FROM projects p
               LEFT JOIN project_fields pf ON p.id = pf.project_id
               WHERE p.id = $1
               GROUP BY p.id""",
            project_id
        )
        return dict(project) if project else None

    async def get_mind_map_projects(self, mind_map_id: UUID, visible_only: bool = True) -> List[dict]:
        query = """
            SELECT p.*, array_agg(DISTINCT pf.field_id) as fields
            FROM projects p
            LEFT JOIN project_fields pf ON p.id = pf.project_id
            WHERE p.mind_map_id = $1 AND p.parent_id IS NULL
        """
        if visible_only:
            query += " AND p.is_visible = true"

        query += " GROUP BY p.id ORDER BY p.importance_score DESC"

        projects = await db.fetch(query, mind_map_id)
        return [dict(p) for p in projects]

    async def get_project_nodes(self, parent_id: UUID, limit: int = 3) -> List[dict]:
        nodes = await db.fetch(
            """SELECT p.*, array_agg(DISTINCT pf.field_id) as fields
               FROM projects p
               LEFT JOIN project_fields pf ON p.id = pf.project_id
               WHERE p.parent_id = $1 AND p.is_visible = true
               GROUP BY p.id
               ORDER BY p.importance_score DESC, p.is_core_issue DESC
               LIMIT $2""",
            parent_id, limit
        )
        return [dict(n) for n in nodes]

    async def update_project(self, project_id: UUID, **kwargs):
        updates = []
        params = []
        param_count = 1

        for key, value in kwargs.items():
            if value is not None and key != "fields":
                updates.append(f"{key} = ${param_count}")
                params.append(value)
                param_count += 1

        if updates:
            params.append(project_id)
            query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ${param_count}"
            await db.execute(query, *params)

        if "fields" in kwargs and kwargs["fields"]:
            await db.execute("DELETE FROM project_fields WHERE project_id = $1", project_id)
            for field_id in kwargs["fields"]:
                await db.execute(
                    "INSERT INTO project_fields (project_id, field_id) VALUES ($1, $2)",
                    project_id, field_id
                )

        logger.info(f"Updated project {project_id}")

    async def create_connection(
            self,
            mind_map_id: UUID,
            connection_type: str,
            from_id: UUID,
            to_id: UUID,
            strength: str = "medium",
            root_cause_id: Optional[UUID] = None
    ) -> UUID:
        conn_id = await db.fetchval(
            """INSERT INTO connections (mind_map_id, connection_type, from_id, to_id, strength, root_cause_id)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
            mind_map_id, connection_type, from_id, to_id, strength, root_cause_id
        )
        logger.info(f"Created connection {conn_id}: {connection_type} from {from_id} to {to_id}")
        return conn_id

    async def get_mind_map_connections(self, mind_map_id: UUID, limit: int = 7) -> List[dict]:
        connections = await db.fetch(
            """SELECT id, connection_type, from_id, to_id, strength, root_cause_id
               FROM connections
               WHERE mind_map_id = $1
               ORDER BY created_at DESC
               LIMIT $2""",
            mind_map_id, limit
        )
        return [dict(c) for c in connections]


project_repository = ProjectRepository()
