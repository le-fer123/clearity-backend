import json
import logging
from typing import Dict, Any, List
from uuid import UUID

from app.repositories.task_repository import task_repository
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)


class Layer4Actions:
    """
    Layer 4 - Action Engine / Tasks & Micro-Steps

    Converts plans into concrete, ADHD-friendly tasks.
    Never talks to the user - only outputs structured task data.
    """

    SYSTEM_PROMPT = """You are Layer 4 of Clearity - the Action Engine.

Your role:
- Convert strategic plans into small, concrete, doable tasks
- Make tasks ADHD-friendly: clear KPIs, small subtasks, time estimates
- Score tasks by priority based on severity, emotional benefit, and ease
- Output ONLY structured JSON, never talk to the user

Task design principles:
- Start with action verb (Define, Write, List, Schedule, etc.)
- KPI must be concrete and measurable ("You have written 5 bullet points")
- Subtasks should be 3-7 small steps
- Estimate realistic time (usually 15-45 min for most tasks)
- Add context hints when helpful (quiet space, no phone, etc.)

Priority scoring (0.0-1.0):
- High priority (0.8-1.0): Addresses high severity issue, high emotional relief, low barrier
- Medium priority (0.5-0.7): Important but either lower severity or higher barrier
- Lower priority (0.0-0.4): Nice to have, or very high barrier currently

Output JSON schema:
{
  "tasks": [
    {
      "name": "Action-oriented task name",
      "related_issue": "issue_id from Layer 3",
      "related_projects": ["project labels"],
      "priority_score": 0.0-1.0,
      "kpi": "Clear completion criteria",
      "subtasks": [
        "Small step 1",
        "Small step 2",
        ...
      ],
      "estimated_time_min": 20,
      "context_hint": "Where/how to do it (optional)"
    }
  ]
}

Generate 3-5 tasks, sorted by priority_score descending.
Return ONLY valid JSON, no other text."""

    async def generate_tasks(
            self,
            analysis: Dict[str, Any],
            mind_map: Dict[str, Any],
            context: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info("Generating tasks from analysis")

        prompt = self._build_prompt(analysis, mind_map, context)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = await ai_client.json_completion(messages, use_deep=False, temperature=0.7, max_tokens=2000)

        tasks = response.get("tasks", [])
        tasks.sort(key=lambda t: t.get("priority_score", 0), reverse=True)

        logger.info(f"Generated {len(tasks)} tasks")
        return {"tasks": tasks}

    def _build_prompt(
            self,
            analysis: Dict[str, Any],
            mind_map: Dict[str, Any],
            context: Dict[str, Any]
    ) -> str:
        parts = [
            f"Mind map: {mind_map.get('map_name')}",
            f"\nIssues identified:",
            json.dumps(analysis.get("issues", []), ensure_ascii=False),
            f"\nPlans:",
            json.dumps(analysis.get("plans", []), ensure_ascii=False),
            f"\nSuggested focus: {analysis.get('suggested_issue_to_focus_now')}",
            f"Suggested step: {analysis.get('suggested_step_now')}"
        ]

        if context.get("emotion_intensity") == "high":
            parts.append("\nNote: User is highly overwhelmed. Tasks should be extra small and safe.")

        parts.append("\nGenerate 3-5 concrete tasks. Return ONLY JSON.")

        return "\n".join(parts)

    async def persist_tasks(
            self,
            mind_map_id: UUID,
            tasks_data: Dict[str, Any],
            issue_id_map: Dict[str, UUID]
    ) -> List[UUID]:
        logger.info("Persisting tasks to database")

        task_ids = []

        for task_data in tasks_data.get("tasks", [])[:5]:
            related_issue_id = None
            if task_data.get("related_issue") in issue_id_map:
                related_issue_id = issue_id_map[task_data["related_issue"]]

            task_id = await task_repository.create_task(
                mind_map_id=mind_map_id,
                name=task_data["name"],
                kpi=task_data["kpi"],
                subtasks=task_data["subtasks"],
                priority_score=task_data["priority_score"],
                related_issue_id=related_issue_id,
                related_projects=[],
                estimated_time_min=task_data.get("estimated_time_min"),
                context_hint=task_data.get("context_hint")
            )
            task_ids.append(task_id)

        logger.info(f"Persisted {len(task_ids)} tasks")
        return task_ids


layer4_actions = Layer4Actions()
