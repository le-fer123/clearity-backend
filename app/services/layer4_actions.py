import json
import logging
from typing import Dict, Any, List
from uuid import UUID

from app.repositories.task_repository import task_repository
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)


class Layer4Actions:
    """
    Layer 4 - Reasoning & Actions (Merged Layer 3 + 4)
    
    Analyzes mind map, identifies issues, root causes, and generates concrete tasks.
    Combines strategic analysis with actionable micro-steps.
    Never talks to the user - only outputs structured data.
    """

    SYSTEM_PROMPT = """You are Layer 4 of Clearity - the Reasoning & Action Engine.

Your role:
- Analyze mind map to identify what's wrong and WHY
- Identify issues, root causes, and build strategic plans
- Convert plans into small, concrete, ADHD-friendly tasks
- Score tasks by priority and suggest what to focus on NOW
- Output ONLY structured JSON, never talk to the user

Common issue types:
- focus_conflict: too many options, no clear selection rule
- unclear_goal: doesn't know what "good" looks like
- energy_drain: not enough energy to maintain everything
- avoidance: knows what to do but avoids it
- decision_overload: paralyzed by too many choices
- validation_anxiety: fears making wrong choice

Common root causes:
- fear_wrong_choice: fears choosing wrong direction
- decision_overload: too many simultaneous decisions
- perfectionism: nothing feels good enough
- low_energy: burnt out, no fuel left
- unclear_values: doesn't know what matters most
- external_pressure: responding to others' expectations

Task design principles:
- **STRICT BAN ON PLANNING**: Do NOT generate tasks starting with "Define", "Plan", "Decide", "Think", "Review", "Strategy".
- **ONLY REAL WORLD ACTIONS**: Tasks must interact with the world.
  - ❌ BAD: "Define engagement strategy"
  - ✅ GOOD: "Post intro on r/books", "Email 5 local librarians", "Setup Google Ads account"
- **NAME NAMES**: You MUST include specific platform names, tools, or URLs allowed by your knowledge.
  - If user describes a book startup, suggested tasks MUST mention "Goodreads", "LibraryThing", "TikTok BookTok".
- KPI must be numeric and binary ("3 emails sent", not "strategy defined").

Priority scoring (0.0-1.0):
- High priority (0.8-1.0): Addresses high severity issue, high emotional relief, low barrier
- Medium priority (0.5-0.7): Important but either lower severity or higher barrier
- Lower priority (0.0-0.4): Nice to have, or very high barrier currently

Output JSON schema:
{
  "issues": [
    {
      "id": "issue_type_name",
      "description": "clear explanation",
      "projects": ["project labels affected"],
      "severity": "low|medium|high"
    }
  ],
  "root_causes": [
    {
      "id": "cause_name",
      "short_explanation": "why this causes problems",
      "linked_issues": ["issue_id1", "issue_id2"]
    }
  ],
  "plans": [
    {
      "issue_id": "issue_type_name",
      "goal": "What we're trying to achieve",
      "steps": ["Step 1 description", "Step 2...", ...]
    }
  ],
  "tasks": [
    {
      "name": "Action-oriented task name",
      "related_issue": "issue_id",
      "related_projects": ["project labels"],
      "priority_score": 0.0-1.0,
      "kpi": "Clear completion criteria",
      "subtasks": ["Small step 1", "Small step 2", ...],
      "estimated_time_min": 20,
      "context_hint": "Where/how to do it (optional)"
    }
  ],
  "suggested_issue_to_focus_now": "issue_id",
  "suggested_step_now": "specific actionable step description",
  "connection_signals": [
    {
      "type": "dependency|conflict|shared_root_cause",
      "from": "project/node label",
      "to": "project/node label",
      "reason": "why connected"
    }
  ]
}

Generate 3-5 tasks, sorted by priority_score descending.
Return ONLY valid JSON, no other text."""

    async def analyze_and_generate_tasks(
            self,
            mind_map: Dict[str, Any],
            context: Dict[str, Any],
            user_message: str
    ) -> Dict[str, Any]:
        """
        Combined analysis: identifies issues, root causes, plans, and generates tasks.
        Replaces separate Layer 3 and Layer 4 calls.
        """
        logger.info("Running combined reasoning & task generation")

        prompt = self._build_prompt(mind_map, context, user_message)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        # Use deep model for combined analysis + task generation
        response = await ai_client.json_completion(
            messages, 
            use_deep=True,
            temperature=0.65,
            max_tokens=4000
        )

        tasks = response.get("tasks", [])
        tasks.sort(key=lambda t: t.get("priority_score", 0), reverse=True)
        response["tasks"] = tasks

        logger.info(
            f"Analysis complete: {len(response.get('issues', []))} issues, "
            f"{len(response.get('root_causes', []))} root causes, "
            f"{len(tasks)} tasks"
        )
        return response

    def _build_prompt(
            self,
            mind_map: Dict[str, Any],
            context: Dict[str, Any],
            user_message: str
    ) -> str:
        parts = [
            f"User message: {user_message}",
            f"\nMind map:",
            f"Name: {mind_map.get('map_name')}",
            f"Theme: {mind_map.get('central_theme')}",
            f"\nProjects: {json.dumps(mind_map.get('projects', []), ensure_ascii=False)}"
        ]

        if context.get("emotion"):
            parts.append(
                f"\nUser emotion: {context['emotion']} "
                f"(intensity: {context.get('emotion_intensity')})"
            )

        if context.get("summary"):
            parts.append(f"Context: {context['summary']}")

        if context.get("emotion_intensity") == "high":
            parts.append("\nNote: User is highly overwhelmed. Tasks should be extra small and safe.")

        parts.append(
            "\nAnalyze what's wrong, why, build plans, and generate 3-5 concrete tasks. "
            "Return ONLY JSON."
        )

        return "\n".join(parts)

    async def persist_analysis_and_tasks(
            self,
            mind_map_id: UUID,
            response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Persist both analysis (issues, root causes, plans) and tasks to database.
        Returns mapping of issue IDs for reference.
        """
        logger.info("Persisting analysis and tasks to database")

        issue_id_map = {}

        # Persist issues
        for issue_data in response.get("issues", []):
            issue_id = await task_repository.create_issue(
                mind_map_id=mind_map_id,
                issue_type=issue_data["id"],
                description=issue_data["description"],
                severity=issue_data.get("severity", "medium"),
                project_ids=[]
            )
            issue_id_map[issue_data["id"]] = issue_id

        # Persist root causes
        for cause_data in response.get("root_causes", []):
            linked_issue_ids = [
                issue_id_map[issue_id]
                for issue_id in cause_data.get("linked_issues", [])
                if issue_id in issue_id_map
            ]

            await task_repository.create_root_cause(
                mind_map_id=mind_map_id,
                cause_id=cause_data["id"],
                explanation=cause_data["short_explanation"],
                linked_issues=linked_issue_ids
            )

        # Persist plans
        for plan_data in response.get("plans", []):
            if plan_data["issue_id"] in issue_id_map:
                await task_repository.create_plan(
                    issue_id=issue_id_map[plan_data["issue_id"]],
                    steps=plan_data.get("steps", [])
                )

        # Persist tasks
        task_ids = []
        for task_data in response.get("tasks", [])[:5]:
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

        logger.info(
            f"Persisted: {len(issue_id_map)} issues, "
            f"{len(response.get('root_causes', []))} root causes, "
            f"{len(task_ids)} tasks"
        )

        return {
            "issue_id_map": issue_id_map,
            "task_ids": task_ids
        }


layer4_actions = Layer4Actions()
