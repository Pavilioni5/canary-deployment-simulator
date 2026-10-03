"""
Pydantic schemas for User Authentication and Role-Based Authorization.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="Unique email address", examples=["engineer@canary.local"])
    password: str = Field(..., min_length=6, description="Minimum 6 characters password", examples=["SecurePass123!"])
    full_name: Optional[str] = Field(None, examples=["DevOps Engineer"])
    role: Optional[str] = Field("USER", description="User role: USER or ADMIN", examples=["USER"])


class UserLoginRequest(BaseModel):
    email: str = Field(..., examples=["engineer@canary.local"])
    password: str = Field(..., examples=["SecurePass123!"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user_id: int
    email: str
    role: str
    full_name: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
