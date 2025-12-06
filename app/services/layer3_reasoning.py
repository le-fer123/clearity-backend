import json
import logging
from typing import Dict, Any
from uuid import UUID

from app.repositories.task_repository import task_repository
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)


class Layer3Reasoning:
    """
    Layer 3 - Reasoning / Why You're Stuck & Plan Builder

    Analyzes the mind map to understand what's wrong and why.
    Builds plans to resolve issues.
    Never talks to the user - only outputs structured analysis.
    """

    SYSTEM_PROMPT = """You are Layer 3 of Clearity - the Reasoning Engine.

Your role:
- Analyze the mind map to identify what's wrong and WHY
- Identify issues, root causes, and build multi-step plans
- Determine which issue to focus on now
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

Your analysis should:
1. Identify 1-3 key issues per mind map
2. Link issues to root causes
3. Create 2-5 step plans for each major issue
4. Suggest which issue/step to focus on NOW based on severity, emotional weight, and user readiness
5. Define connections for mind map visualization (dependency/conflict/shared_root_cause)

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
      "steps": ["Step 1 description", "Step 2...", ...]
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

Return ONLY valid JSON, no other text."""

    async def analyze(
            self,
            mind_map: Dict[str, Any],
            context: Dict[str, Any],
            user_message: str
    ) -> Dict[str, Any]:
        logger.info("Analyzing mind map for issues and root causes")

        prompt = self._build_prompt(mind_map, context, user_message)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = await ai_client.json_completion(messages, use_deep=True, temperature=0.6, max_tokens=3000)

        logger.info(
            f"Analysis complete: {len(response.get('issues', []))} issues, {len(response.get('root_causes', []))} root causes")
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
            parts.append(f"\nUser emotion: {context['emotion']} (intensity: {context.get('emotion_intensity')})")

        if context.get("summary"):
            parts.append(f"Context: {context['summary']}")

        parts.append("\nAnalyze what's wrong, why, and suggest what to focus on. Return ONLY JSON.")

        return "\n".join(parts)

    async def persist_analysis(
            self,
            mind_map_id: UUID,
            analysis: Dict[str, Any]
    ) -> Dict[str, UUID]:
        logger.info("Persisting analysis to database")

        issue_id_map = {}

        for issue_data in analysis.get("issues", []):
            issue_id = await task_repository.create_issue(
                mind_map_id=mind_map_id,
                issue_type=issue_data["id"],
                description=issue_data["description"],
                severity=issue_data.get("severity", "medium"),
                project_ids=[]
            )
            issue_id_map[issue_data["id"]] = issue_id

        for cause_data in analysis.get("root_causes", []):
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

        for plan_data in analysis.get("plans", []):
            if plan_data["issue_id"] in issue_id_map:
                await task_repository.create_plan(
                    issue_id=issue_id_map[plan_data["issue_id"]],
                    steps=plan_data["steps"]
                )

        logger.info(f"Analysis persisted: {len(issue_id_map)} issues")
        return issue_id_map


layer3_reasoning = Layer3Reasoning()
