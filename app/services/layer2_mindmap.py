import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from app.repositories.mindmap_repository import mindmap_repository
from app.repositories.project_repository import project_repository
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)


class Layer2MindMap:
    """
    Layer 2 - Visualization / Mind Map Builder

    Maintains the living mind map that mirrors the user's brain.
    Never talks to the user - only outputs structured JSON.
    """

    SYSTEM_PROMPT = """You are Layer 2 of Clearity - the Mind Map Builder.

Your role:
- Build and update a living mind map representing the user's mental state
- Output ONLY structured JSON, never talk to the user
- Show what's in the user's mind RIGHT NOW
- Use predefined fields with these EXACT IDs (do not add any prefixes):
  * startups → Startups
  * career → Career
  * education → Education
  * health → Health
  * mental_health → Mental Health
  * relationships → Relationships
  * money → Money
  * family → Family
  * personal_growth → Personal Growth
- Max 5 visible projects, max 3 visible nodes per project
- Assign emotions and colors to nodes based on emotional context
- Calculate project colors from node emotions (weighted average)
- Identify issue severity (none/low/medium/high) for red dot visualization

Emotion to color mapping:
- overwhelm/anxiety/stress → red
- frustration/chaos/confusion → orange
- uncertainty/doubt/ambivalence → yellow
- hope/progress/clarity → green
- calm/stability/control → blue
- excitement/passion/creativity → purple
- unknown/not enough data → grey

Rules:
- Reuse existing projects/nodes when continuing a session
- NEVER change map_name once set
- Select most important 3 nodes per project based on emotional weight and relevance
- Group similar projects when needed to stay under 5 visible projects
- Set is_core_issue=true for nodes central to being stuck
- IMPORTANT: Use field IDs EXACTLY as listed above (e.g., "startups" NOT "fld_startups")
- Naming Rule: Use CONCRETE labels. Instead of "Promotion", use "Reddit Ads" or "Cold Email". Instead of "Health", use "Sleep 8h" or "Back Pain". Be specific.

Output JSON schema:
{
  "map_name": "short phrase describing main reason user came",
  "central_theme": "what this is about",
  "fields": [{"id": "field_id", "label": "Field Name"}],
  "projects": [
    {
      "id": "uuid or reused id",
      "label": "Project Name",
      "fields": ["field_id"],
      "emotion": "color",
      "clarity": "low|medium|high",
      "issue_severity": "none|low|medium|high",
      "status": "active",
      "importance_score": 0.0-1.0,
      "nodes": [
        {
          "id": "uuid or reused id",
          "label": "Node description",
          "emotion": "color",
          "importance_score": 0.0-1.0,
          "is_core_issue": true/false,
          "fields": ["field_id"]
        }
      ]
    }
  ],
  "connections": [
    {
      "type": "dependency|shared_root_cause|conflict",
      "from_id": "uuid",
      "to_id": "uuid",
      "strength": "low|medium|high",
      "root_cause_id": "uuid or null"
    }
  ]
}

Return ONLY valid JSON, no other text."""

    async def build_mind_map(
            self,
            user_message: str,
            context: Dict[str, Any],
            existing_map: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        logger.info("Building/updating mind map")

        prompt = self._build_prompt(user_message, context, existing_map)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = await ai_client.json_completion(messages, use_deep=False, temperature=0.5, max_tokens=5000)

        logger.info(f"Mind map built: {response.get('map_name', 'Unnamed')}")
        return response

    def _build_prompt(
            self,
            user_message: str,
            context: Dict[str, Any],
            existing_map: Optional[Dict[str, Any]]
    ) -> str:
        parts = [f"User message: {user_message}"]

        if context.get("emotion"):
            parts.append(
                f"User emotion: {context['emotion']} (intensity: {context.get('emotion_intensity', 'medium')})")

        if context.get("summary"):
            parts.append(f"Session summary: {context['summary']}")

        if existing_map:
            parts.append(f"\nExisting mind map to update:")
            parts.append(f"Map name: {existing_map.get('map_name', 'Unnamed')}")
            parts.append(f"Central theme: {existing_map.get('central_theme', '')}")
            parts.append(f"Current projects: {json.dumps(existing_map.get('projects', []), ensure_ascii=False)}")
            parts.append("\nIMPORTANT: Reuse project/node IDs where possible. Do NOT change map_name.")
        else:
            parts.append("\nThis is a new mind map. Create map_name and central_theme based on user's message.")

        parts.append("\nBuild/update the mind map and return ONLY JSON.")

        return "\n".join(parts)

    async def persist_mind_map(
            self,
            session_id: UUID,
            mind_map_data: Dict[str, Any],
            existing_mind_map_id: Optional[UUID] = None
    ) -> UUID:
        logger.info("Persisting mind map to database")

        if existing_mind_map_id:
            mind_map_id = existing_mind_map_id
            await mindmap_repository.update_mind_map(
                mind_map_id=mind_map_id,
                map_name=mind_map_data["map_name"],
                central_theme=mind_map_data["central_theme"]
            )
        else:
            mind_map_id = await mindmap_repository.create_mind_map(
                session_id=session_id,
                map_name=mind_map_data["map_name"],
                central_theme=mind_map_data["central_theme"]
            )

        # Map AI-generated IDs to real database UUIDs
        id_mapping = {}  # {ai_id: db_uuid}

        for project_data in mind_map_data.get("projects", []):
            project_id = await self._persist_project(mind_map_id, project_data, id_mapping)

        for conn in mind_map_data.get("connections", []):
            await self._persist_connection(mind_map_id, conn, id_mapping)

        logger.info(f"Mind map {mind_map_id} persisted successfully")
        return mind_map_id

    async def _persist_project(
            self,
            mind_map_id: UUID,
            project_data: Dict[str, Any],
            id_mapping: Dict[str, UUID],
            parent_id: Optional[UUID] = None
    ) -> UUID:
        project_id = await project_repository.create_project(
            mind_map_id=mind_map_id,
            label=project_data["label"],
            fields=project_data.get("fields", []),
            emotion=project_data.get("emotion", "grey"),
            parent_id=parent_id,
            clarity=project_data.get("clarity"),
            issue_severity=project_data.get("issue_severity", "none"),
            importance_score=project_data.get("importance_score", 0.5),
            is_core_issue=project_data.get("is_core_issue", False),
            is_visible=True
        )

        # Map AI-generated project ID to real database UUID
        if "id" in project_data and project_data["id"]:
            id_mapping[str(project_data["id"])] = project_id

        # Create nodes and map their IDs too
        for node_data in project_data.get("nodes", []):
            node_id = await project_repository.create_project(
                mind_map_id=mind_map_id,
                label=node_data["label"],
                fields=node_data.get("fields", project_data.get("fields", [])),
                emotion=node_data.get("emotion", "grey"),
                parent_id=project_id,
                importance_score=node_data.get("importance_score", 0.5),
                is_core_issue=node_data.get("is_core_issue", False),
                is_visible=True
            )
            # Map AI-generated node ID to real database UUID
            if "id" in node_data and node_data["id"]:
                id_mapping[str(node_data["id"])] = node_id

        return project_id

    async def _persist_connection(self, mind_map_id: UUID, conn: Dict[str, Any], id_mapping: Dict[str, UUID]):
        # Map AI-generated IDs to real database UUIDs
        from_id_str = str(conn["from_id"])
        to_id_str = str(conn["to_id"])
        
        from_id = id_mapping.get(from_id_str)
        to_id = id_mapping.get(to_id_str)
        
        # Skip connection if either ID is not found in mapping
        if not from_id or not to_id:
            logger.warning(f"Skipping connection: from_id={from_id_str} or to_id={to_id_str} not found in ID mapping")
            return
        
        root_cause_id = None
        if conn.get("root_cause_id"):
            root_cause_id_str = str(conn["root_cause_id"])
            root_cause_id = id_mapping.get(root_cause_id_str)
        
        await project_repository.create_connection(
            mind_map_id=mind_map_id,
            connection_type=conn["type"],
            from_id=from_id,
            to_id=to_id,
            strength=conn.get("strength", "medium"),
            root_cause_id=root_cause_id
        )


layer2_mindmap = Layer2MindMap()
