from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FieldSchema(BaseModel):
    id: str
    label: str


class NodeSchema(BaseModel):
    id: UUID
    label: str
    emotion: str
    importance_score: float
    is_core_issue: bool
    parent_id: Optional[UUID]
    fields: List[str]


class ProjectSchema(BaseModel):
    id: UUID
    label: str
    fields: List[str]
    emotion: str
    clarity: Optional[str]
    issue_severity: str
    status: str
    nodes: List[NodeSchema]


class ConnectionSchema(BaseModel):
    type: str
    from_id: UUID
    to_id: UUID
    strength: str
    root_cause_id: Optional[UUID] = None


class MindMapResponse(BaseModel):
    map_name: str
    central_theme: str
    fields: List[FieldSchema]
    projects: List[ProjectSchema]
    connections: List[ConnectionSchema]


class TaskSchema(BaseModel):
    id: UUID
    name: str
    related_issue: Optional[str]
    related_projects: List[UUID]
    priority_score: float
    kpi: str
    subtasks: List[str]
    estimated_time_min: Optional[int]
    context_hint: Optional[str]
    status: str


class IssueSchema(BaseModel):
    id: str
    description: str
    severity: str
    related_projects: List[str]


class RootCauseSchema(BaseModel):
    id: str
    explanation: str
    related_issues: List[str]


class PlanSchema(BaseModel):
    id: str
    issue_id: str
    goal: str
    steps: List[str]


class SnapshotSchema(BaseModel):
    map_name: str
    last_updated: datetime
    summary: Optional[str]
    unresolved_issues: List[str]


class ChatResponse(BaseModel):
    session_id: UUID
    message: str
    mind_map: Optional[MindMapResponse] = None
    suggested_tasks: List[TaskSchema] = []
    metadata: Optional[Dict[str, Any]] = None
    issues: List[IssueSchema] = []
    root_causes: List[RootCauseSchema] = []
    plans: List[PlanSchema] = []
    latest_snapshot: Optional[SnapshotSchema] = None


class SessionResponse(BaseModel):
    session_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class SnapshotCandidate(BaseModel):
    map_id: UUID
    map_name: str
    last_updated: datetime
    summary: str
    unresolved_issues: List[str]
