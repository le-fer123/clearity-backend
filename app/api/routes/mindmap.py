import json
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.models.responses import MindMapResponse, TaskSchema
from app.repositories.mindmap_repository import mindmap_repository
from app.repositories.project_repository import project_repository
from app.repositories.task_repository import task_repository

logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.get("/sessions/{session_id}/mindmap", response_model=MindMapResponse)
async def get_session_mindmap(session_id: UUID):
    """
    Get the current mind map for a session.
    """
    try:
        mind_map = await mindmap_repository.get_session_mind_map(session_id)

        if not mind_map:
            raise HTTPException(status_code=404, detail="Mind map not found for this session")

        mind_map_id = mind_map["id"]
        projects_data = await project_repository.get_mind_map_projects(mind_map_id)
        connections_data = await project_repository.get_mind_map_connections(mind_map_id)

        projects = []
        for proj in projects_data:
            nodes_data = await project_repository.get_project_nodes(proj["id"], limit=3)

            nodes = [
                {
                    "id": node["id"],
                    "label": node["label"],
                    "emotion": node["emotion"],
                    "importance_score": float(node["importance_score"]),
                    "is_core_issue": node["is_core_issue"],
                    "parent_id": node["parent_id"],
                    "fields": node["fields"] if node["fields"] else []
                }
                for node in nodes_data
            ]

            projects.append({
                "id": proj["id"],
                "label": proj["label"],
                "fields": proj["fields"] if proj["fields"] else [],
                "emotion": proj["emotion"],
                "clarity": proj["clarity"],
                "issue_severity": proj["issue_severity"],
                "status": proj["status"],
                "nodes": nodes
            })

        connections = [
            {
                "type": conn["connection_type"],
                "from_id": conn["from_id"],
                "to_id": conn["to_id"],
                "strength": conn["strength"],
                "root_cause_id": conn["root_cause_id"]
            }
            for conn in connections_data
        ]

        fields_set = set()
        for proj in projects:
            fields_set.update(proj["fields"])

        fields = [{"id": fid, "label": fid.replace("_", " ").title()} for fid in fields_set]

        return MindMapResponse(
            map_name=mind_map["map_name"],
            central_theme=mind_map["central_theme"],
            fields=fields,
            projects=projects,
            connections=connections
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mind map: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting mind map: {str(e)}")


@router.get("/sessions/{session_id}/tasks", response_model=list[TaskSchema])
async def get_session_tasks(session_id: UUID, limit: int = 5):
    """
    Get suggested tasks for a session.
    """
    try:
        mind_map = await mindmap_repository.get_session_mind_map(session_id)

        if not mind_map:
            raise HTTPException(status_code=404, detail="No mind map found for this session")

        tasks_data = await task_repository.get_mind_map_tasks(mind_map["id"], limit=limit)

        tasks = []
        for task in tasks_data:
            subtasks = parse_json_field(task["subtasks"])
            tasks.append(TaskSchema(
                id=task["id"],
                name=task["name"],
                related_issue=None,
                related_projects=[pid for pid in (task.get("related_projects") or []) if pid],
                priority_score=float(task["priority_score"]),
                kpi=task["kpi"],
                subtasks=subtasks if isinstance(subtasks, list) else [],
                estimated_time_min=task["estimated_time_min"],
                context_hint=task["context_hint"],
                status=task["status"]
            ))

        return tasks

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting tasks: {str(e)}")
