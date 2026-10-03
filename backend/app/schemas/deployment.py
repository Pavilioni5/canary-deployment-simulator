"""
Pydantic schemas for Deployment CRUD, Versions, and Traffic Configuration.
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DeploymentVersionCreate(BaseModel):
    version_tag: str = Field(..., examples=["v1.0.0"])
    simulated_latency_ms: float = Field(50.0, ge=0.0, examples=[50.0])
    failure_rate: float = Field(0.0, ge=0.0, le=1.0, description="Failure probability between 0.0 and 1.0", examples=[0.0])


class DeploymentVersionResponse(BaseModel):
    id: int
    deployment_id: int
    version_tag: str
    version_type: str  # "STABLE" or "CANARY"
    image_tag: str
    simulated_latency_ms: float
    failure_rate: float
    is_active: bool
    created_at: datetime


class TrafficConfigResponse(BaseModel):
    id: int
    deployment_id: int
    stable_percentage: float
    canary_percentage: float
    last_shifted_at: datetime
    updated_at: datetime


class DeploymentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Payment Gateway Microservice"])
    description: Optional[str] = Field(None, examples=["Canary rollout of optimized checkout engine v2"])
    rollback_threshold: float = Field(10.0, ge=1.0, le=100.0, description="Error rate percentage threshold that triggers auto-rollback", examples=[10.0])
    evaluation_window_seconds: int = Field(60, ge=10, le=3600, examples=[60])
    stable_tag: str = Field("v1.0.0", examples=["v1.0.0"])
    canary_tag: str = Field("v2.0.0", examples=["v2.0.0"])
    stable_latency_ms: float = Field(50.0, ge=0.0, examples=[45.0])
    canary_latency_ms: float = Field(50.0, ge=0.0, examples=[48.0])
    initial_canary_failure_rate: float = Field(0.0, ge=0.0, le=1.0, examples=[0.0])


class DeploymentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    rollback_threshold: Optional[float] = Field(None, ge=1.0, le=100.0)
    evaluation_window_seconds: Optional[int] = Field(None, ge=10, le=3600)


class DeploymentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str  # PENDING, RUNNING, COMPLETED, ROLLED_BACK
    rollback_threshold: float
    evaluation_window_seconds: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class DeploymentDetailResponse(DeploymentResponse):
    versions: List[DeploymentVersionResponse] = []
    traffic_config: Optional[TrafficConfigResponse] = None
