from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: Optional[str] = None


class UserInfoResponse(BaseModel):
    user_id: UUID
    email: Optional[str]
    is_anonymous: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
