"""
Pydantic schemas for System and Health check responses.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SystemInfoResponse(BaseModel):
    project: str = Field(..., examples=["Cloud-Based Canary Deployment Simulator"])
    project_id: str = Field(..., examples=["P71"])
    version: str = Field(..., examples=["1.0.0"])
    status: str = Field(..., examples=["operational"])
    environment: str = Field(..., examples=["development"])
    docs_url: str = Field(..., examples=["/docs"])
    timestamp: datetime = Field(default_factory=utc_now)


class ComponentHealth(BaseModel):
    status: str = Field(..., examples=["healthy"])
    message: Optional[str] = Field(None, examples=["Component responsive"])
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    environment: str = Field(..., examples=["development"])
    timestamp: datetime = Field(default_factory=utc_now)
    uptime_seconds: float = Field(..., examples=[120.5])


class DetailedHealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    timestamp: datetime = Field(default_factory=utc_now)
    uptime_seconds: float = Field(...)
    components: Dict[str, ComponentHealth] = Field(...)
