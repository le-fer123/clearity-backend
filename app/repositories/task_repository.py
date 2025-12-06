import json
import logging
from typing import List, Optional
from uuid import UUID

from app.database import db

logger = logging.getLogger(__name__)


class TaskRepository:
    async def create_task(
            self,
            mind_map_id: UUID,
            name: str,
            kpi: str,
            subtasks: List[str],
            priority_score: float,
            related_issue_id: Optional[UUID] = None,
            related_projects: List[UUID] = None,
            estimated_time_min: Optional[int] = None,
            context_hint: Optional[str] = None
    ) -> UUID:
        task_id = await db.fetchval(
            """INSERT INTO tasks (mind_map_id, name, related_issue_id, priority_score, kpi,
               subtasks, estimated_time_min, context_hint)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
            mind_map_id, name, related_issue_id, priority_score, kpi,
            json.dumps(subtasks), estimated_time_min, context_hint
        )

        if related_projects:
            for project_id in related_projects:
                await db.execute(
                    "INSERT INTO task_projects (task_id, project_id) VALUES ($1, $2)",
                    task_id, project_id
                )

        logger.info(f"Created task {task_id}: {name}")
        return task_id

    async def get_mind_map_tasks(self, mind_map_id: UUID, limit: int = 5) -> List[dict]:
        tasks = await db.fetch(
            """SELECT t.*, array_agg(tp.project_id) FILTER (WHERE tp.project_id IS NOT NULL) as related_projects
               FROM tasks t
               LEFT JOIN task_projects tp ON t.id = tp.task_id
               WHERE t.mind_map_id = $1
               GROUP BY t.id
               ORDER BY t.priority_score DESC, t.created_at DESC
               LIMIT $2""",
            mind_map_id, limit
        )
        return [dict(t) for t in tasks]

    async def update_task_status(self, task_id: UUID, status: str):
        await db.execute(
            "UPDATE tasks SET status = $1 WHERE id = $2",
            status, task_id
        )
        logger.info(f"Updated task {task_id} status to {status}")

    async def create_issue(self, mind_map_id: UUID, issue_type: str, description: str, severity: str,
                           project_ids: List[UUID] = None) -> UUID:
        issue_id = await db.fetchval(
            "INSERT INTO issues (mind_map_id, issue_type, description, severity) VALUES ($1, $2, $3, $4) RETURNING id",
            mind_map_id, issue_type, description, severity
        )

        if project_ids:
            for project_id in project_ids:
                await db.execute(
                    "INSERT INTO issue_projects (issue_id, project_id) VALUES ($1, $2)",
                    issue_id, project_id
                )

        logger.info(f"Created issue {issue_id}: {issue_type}")
        return issue_id

    async def create_root_cause(self, mind_map_id: UUID, cause_id: str, explanation: str,
                                linked_issues: List[UUID] = None) -> UUID:
        root_cause_id = await db.fetchval(
            "INSERT INTO root_causes (mind_map_id, cause_id, short_explanation) VALUES ($1, $2, $3) RETURNING id",
            mind_map_id, cause_id, explanation
        )

        if linked_issues:
            for issue_id in linked_issues:
                await db.execute(
                    "INSERT INTO root_cause_issues (root_cause_id, issue_id) VALUES ($1, $2)",
                    root_cause_id, issue_id
                )

        logger.info(f"Created root cause {root_cause_id}: {cause_id}")
        return root_cause_id

    async def create_plan(self, issue_id: UUID, steps: List[str]) -> UUID:
        plan_id = await db.fetchval(
            "INSERT INTO plans (issue_id, steps) VALUES ($1, $2) RETURNING id",
            issue_id, json.dumps(steps)
        )
        logger.info(f"Created plan {plan_id} for issue {issue_id}")
        return plan_id

    async def get_mind_map_issues(self, mind_map_id: UUID) -> List[dict]:
        issues = await db.fetch(
            """SELECT i.*, array_agg(ip.project_id) FILTER (WHERE ip.project_id IS NOT NULL) as project_ids
               FROM issues i
               LEFT JOIN issue_projects ip ON i.id = ip.issue_id
               WHERE i.mind_map_id = $1
               GROUP BY i.id
               ORDER BY i.created_at DESC""",
            mind_map_id
        )
        return [dict(i) for i in issues]

    async def get_mind_map_root_causes(self, mind_map_id: UUID) -> List[dict]:
        root_causes = await db.fetch(
            """SELECT rc.*, array_agg(rci.issue_id) FILTER (WHERE rci.issue_id IS NOT NULL) as linked_issue_ids
               FROM root_causes rc
               LEFT JOIN root_cause_issues rci ON rc.id = rci.root_cause_id
               WHERE rc.mind_map_id = $1
               GROUP BY rc.id
               ORDER BY rc.created_at DESC""",
            mind_map_id
        )
        return [dict(rc) for rc in root_causes]

    async def get_issue_plans(self, issue_id: UUID) -> List[dict]:
        plans = await db.fetch(
            "SELECT * FROM plans WHERE issue_id = $1 ORDER BY created_at DESC",
            issue_id
        )
        return [dict(p) for p in plans]

    async def get_mind_map_plans(self, mind_map_id: UUID) -> List[dict]:
        plans = await db.fetch(
            """SELECT p.*, i.issue_type, i.id as issue_db_id
               FROM plans p
               JOIN issues i ON p.issue_id = i.id
               WHERE i.mind_map_id = $1
               ORDER BY p.created_at DESC""",
            mind_map_id
        )
        return [dict(p) for p in plans]


task_repository = TaskRepository()
