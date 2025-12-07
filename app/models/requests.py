from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    message: str = Field(..., min_length=1, max_length=5000)


class CreateSessionRequest(BaseModel):
    user_id: Optional[UUID] = None
