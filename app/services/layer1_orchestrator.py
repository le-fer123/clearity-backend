import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.repositories.message_repository import message_repository
from app.repositories.mindmap_repository import mindmap_repository
from app.repositories.project_repository import project_repository
from app.repositories.session_repository import session_repository
from app.repositories.task_repository import task_repository
from app.services.ai_client import ai_client
from app.services.layer2_mindmap import layer2_mindmap
from app.services.layer4_actions import layer4_actions  # Merged Layer 3 + 4
from app.services.layer5_memory import layer5_memory

logger = logging.getLogger(__name__)


def parse_json_field(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON field: {e}. Value: {value[:100]}")
            return value
    return value


class Layer1Orchestrator:
    """
    Layer 1 - Support & Orchestrator

    The ONLY layer that talks to the user.
    Orchestrates all other layers.
    Warm, human, calming, slightly casual but smart.
    """

    SYSTEM_PROMPT = """You are Clearity - an AI clarity engine for people who feel mentally overloaded, scattered, or stuck.

Your personality:
- Warm, human, calming, slightly casual but smart
- Make users feel heard, not judged
- Translate internal structure into simple language
- Never overwhelming - pace carefully

Your role:
1. Understand user messages in context (emotion, intensity, intent)
2. Reflect their emotional state ("this sounds heavy/confusing/exciting")
3. Provide short clarity summaries
4. Mention the mind map at high level when relevant
5. Ask 0-2 simple questions if context is missing
6. Offer 0-2 micro-tasks when user is ready
7. NEVER dump everything at once

Pacing rules:
- At most per turn: 1 core insight + 1 focus area + 1-2 micro-actions
- High overwhelm → more validation & explanation, fewer tasks
- Calmer/curious → more structure & next steps

You have access to:
- User's living mind map (fields, projects, nodes, connections)
- Analysis of why they're stuck (issues, root causes)
- Concrete next-step tasks

Your messages should feel like talking to a smart friend who really gets it.
Keep responses concise (2-4 short paragraphs max).
Use simple language, not therapy-speak or corporate buzzwords."""

    async def process_message(
            self,
            session_id: UUID,
            user_id: UUID,
            message: str
    ) -> Dict[str, Any]:
        logger.info(f"Processing message for session {session_id}")

        await message_repository.create_message(session_id, "user", message)
        await session_repository.update_session(session_id)

        # Parallelize independent operations
        context, existing_snapshot = await asyncio.gather(
            self._build_context(session_id, user_id, message),
            layer5_memory.retrieve_latest_snapshot(session_id)
        )
        logger.info(f"Context: emotion={context.get('emotion')}, intent={context.get('user_intent')}")
        existing_map = existing_snapshot["snapshot_data"] if existing_snapshot else None

        mind_map_data = await layer2_mindmap.build_mind_map(message, context, existing_map)

        mind_map_id = await layer2_mindmap.persist_mind_map(
            session_id=session_id,
            mind_map_data=mind_map_data,
            existing_mind_map_id=existing_snapshot["mind_map_id"] if existing_snapshot else None
        )

        # Layer 4 - Combined Reasoning & Tasks (merged Layer 3 + 4)
        analysis_and_tasks = await layer4_actions.analyze_and_generate_tasks(
            mind_map_data, context, message
        )
        
        # Persist analysis and tasks
        persist_result = await layer4_actions.persist_analysis_and_tasks(
            mind_map_id, analysis_and_tasks
        )

        response_message = await self._generate_response(
            message=message,
            context=context,
            mind_map=mind_map_data,
            analysis=analysis_and_tasks,
            tasks={"tasks": analysis_and_tasks.get("tasks", [])}
        )

        await message_repository.create_message(session_id, "assistant", response_message)

        snapshot_data = {
            "map_name": mind_map_data["map_name"],
            "central_theme": mind_map_data["central_theme"],
            "projects": mind_map_data.get("projects", []),
            "issues": analysis_and_tasks.get("issues", []),
            "root_causes": analysis_and_tasks.get("root_causes", [])
        }

        unresolved_issues = [issue["id"] for issue in analysis_and_tasks.get("issues", [])]

        await layer5_memory.store_snapshot(
            session_id=session_id,
            mind_map_id=mind_map_id,
            snapshot_data=snapshot_data,
            progress_notes=None,
            unresolved_issues=unresolved_issues
        )

        mind_map_response = await self._format_mind_map_response(mind_map_id)
        tasks_response = await self._format_tasks_response(mind_map_id)
        analysis_response = await self._format_analysis_response(mind_map_id)
        snapshot_response = await self._format_snapshot_response(mind_map_id)

        logger.info(f"Message processed successfully for session {session_id}")

        return {
            "session_id": session_id,
            "message": response_message,
            "mind_map": mind_map_response,
            "suggested_tasks": tasks_response[:2],
            "metadata": {
                "emotion": context.get("emotion"),
                "emotion_intensity": context.get("emotion_intensity"),
                "suggested_focus": analysis_and_tasks.get("suggested_issue_to_focus_now")
            },
            "issues": analysis_response["issues"],
            "root_causes": analysis_response["root_causes"],
            "plans": analysis_response["plans"],
            "latest_snapshot": snapshot_response
        }

    async def _build_context(self, session_id: UUID, user_id: UUID, message: str) -> Dict[str, Any]:
        recent_messages = await message_repository.get_recent_messages(session_id, limit=15)

        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_messages
        ])

        analysis_prompt = f"""Analyze this user message and conversation context.

Recent conversation:
{conversation_history}

Current user message: {message}

Determine:
1. Primary emotion (overwhelm/anxiety/stress/frustration/confusion/uncertainty/hope/calm/excitement)
2. Emotion intensity (low/medium/high)
3. User intent (venting/understanding/deciding/acting/exploring)
4. Brief summary of situation (1-2 sentences)
5. Session stage (early/middle/established)

Return JSON:
{{
  "emotion": "emotion_name",
  "emotion_intensity": "low|medium|high",
  "user_intent": "intent_type",
  "summary": "brief situation summary",
  "session_stage": "early|middle|established"
}}"""

        messages = [{"role": "user", "content": analysis_prompt}]

        try:
            context = await ai_client.json_completion(messages, use_deep=False, temperature=0.3, max_tokens=1000)
            return context
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            return {
                "emotion": "unknown",
                "emotion_intensity": "medium",
                "user_intent": "understanding",
                "summary": message[:200],
                "session_stage": "early"
            }

    async def _generate_response(
            self,
            message: str,
            context: Dict[str, Any],
            mind_map: Dict[str, Any],
            analysis: Dict[str, Any],
            tasks: Dict[str, Any]
    ) -> str:
        prompt = f"""User message: {message}

User emotional state: {context.get('emotion')} (intensity: {context.get('emotion_intensity')})
User intent: {context.get('user_intent')}

Mind map summary:
- Name: {mind_map.get('map_name')}
- Theme: {mind_map.get('central_theme')}
- Projects: {len(mind_map.get('projects', []))} active areas

Key issue identified: {analysis.get('suggested_issue_to_focus_now')}
Suggested next step: {analysis.get('suggested_step_now')}

Top tasks available:
{json.dumps(tasks.get('tasks', [])[:2], ensure_ascii=False, indent=2)}

Generate a warm, concise response (2-4 short paragraphs):
1. Reflect their emotion briefly
2. Provide 1 core clarity insight about their situation
3. Optionally mention what you see in their mind map
4. Suggest 1-2 micro-actions OR ask 1 clarifying question

Remember: Don't overwhelm. Keep it human and helpful."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = await ai_client.fast_completion(messages, temperature=0.8, max_tokens=600)

        return response.strip()

    async def _format_mind_map_response(self, mind_map_id: UUID) -> Optional[Dict[str, Any]]:
        mind_map = await mindmap_repository.get_mind_map(mind_map_id)
        if not mind_map:
            return None

        projects_data = await project_repository.get_mind_map_projects(mind_map_id, visible_only=True)
        connections_data = await project_repository.get_mind_map_connections(mind_map_id)

        projects = []
        for proj in projects_data[:5]:
            nodes_data = await project_repository.get_project_nodes(proj["id"], limit=3)

            nodes = [
                {
                    "id": str(node["id"]),
                    "label": node["label"],
                    "emotion": node["emotion"],
                    "importance_score": float(node["importance_score"]),
                    "is_core_issue": node["is_core_issue"],
                    "parent_id": str(node["parent_id"]) if node["parent_id"] else None,
                    "fields": node["fields"] if node["fields"] else []
                }
                for node in nodes_data
            ]

            projects.append({
                "id": str(proj["id"]),
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
                "from_id": str(conn["from_id"]),
                "to_id": str(conn["to_id"]),
                "strength": conn["strength"],
                "root_cause_id": str(conn["root_cause_id"]) if conn["root_cause_id"] else None
            }
            for conn in connections_data
        ]

        fields_set = set()
        for proj in projects:
            fields_set.update(proj["fields"])

        fields = [{"id": fid, "label": fid.replace("_", " ").title()} for fid in fields_set]

        return {
            "map_name": mind_map["map_name"],
            "central_theme": mind_map["central_theme"],
            "fields": fields,
            "projects": projects,
            "connections": connections
        }

    async def _format_tasks_response(self, mind_map_id: UUID) -> List[Dict[str, Any]]:
        tasks_data = await task_repository.get_mind_map_tasks(mind_map_id, limit=5)

        tasks = []
        for task in tasks_data:
            subtasks = parse_json_field(task["subtasks"])
            tasks.append({
                "id": str(task["id"]),
                "name": task["name"],
                "related_issue": None,
                "related_projects": [str(pid) for pid in (task.get("related_projects") or []) if pid],
                "priority_score": float(task["priority_score"]),
                "kpi": task["kpi"],
                "subtasks": subtasks if isinstance(subtasks, list) else [],
                "estimated_time_min": task["estimated_time_min"],
                "context_hint": task["context_hint"],
                "status": task["status"]
            })

        return tasks

    async def _format_analysis_response(self, mind_map_id: UUID) -> Dict[str, Any]:
        """Format Layer 3 analysis data (issues, root causes, plans)"""
        issues_data = await task_repository.get_mind_map_issues(mind_map_id)
        root_causes_data = await task_repository.get_mind_map_root_causes(mind_map_id)
        plans_data = await task_repository.get_mind_map_plans(mind_map_id)

        issues = []
        for issue in issues_data:
            project_ids = issue.get("project_ids") or []
            issues.append({
                "id": issue["issue_type"],
                "description": issue["description"],
                "severity": issue["severity"],
                "related_projects": [str(pid) for pid in project_ids if pid]
            })

        root_causes = []
        for rc in root_causes_data:
            linked_issue_ids = rc.get("linked_issue_ids") or []
            root_causes.append({
                "id": rc["cause_id"],
                "explanation": rc["short_explanation"],
                "related_issues": [str(iid) for iid in linked_issue_ids if iid]
            })

        plans = []
        for plan in plans_data:
            steps = parse_json_field(plan["steps"])
            plans.append({
                "id": str(plan["id"]),
                "issue_id": plan["issue_type"],
                "goal": f"Resolve {plan['issue_type']}",
                "steps": steps if isinstance(steps, list) else []
            })

        return {
            "issues": issues,
            "root_causes": root_causes,
            "plans": plans
        }

    async def _format_snapshot_response(self, mind_map_id: UUID) -> Optional[Dict[str, Any]]:
        """Format Layer 5 snapshot data"""
        snapshots = await layer5_memory.get_mind_map_snapshots(mind_map_id, limit=1)

        if not snapshots:
            return None

        snapshot = snapshots[0]
        snapshot_data = snapshot.get("snapshot_data", {})
        unresolved_issues = snapshot.get("unresolved_issues", [])

        return {
            "map_name": snapshot_data.get("map_name", "Unknown"),
            "last_updated": snapshot["last_updated"],
            "summary": snapshot.get("progress_notes"),
            "unresolved_issues": unresolved_issues if isinstance(unresolved_issues, list) else []
        }


layer1_orchestrator = Layer1Orchestrator()
