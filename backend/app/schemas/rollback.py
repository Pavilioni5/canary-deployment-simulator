"""
Pydantic schemas for Manual and Automated Rollback operations.
"""
from datetime import datetime, timezone
from typing import Optional, Dict
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ManualRollbackRequest(BaseModel):
    reason: Optional[str] = Field("Manual operator intervention: rolling back traffic to stable v1.", examples=["Performance anomaly observed in canary instances."])


class RollbackResponse(BaseModel):
    deployment_id: int
    deployment_name: str
    status: str  # "ROLLED_BACK"
    rollback_type: str  # "AUTOMATIC" or "MANUAL"
    reason: str
    rollback_threshold: float
    observed_canary_error_rate: Optional[float] = None
    traffic_restored: Dict[str, float] = Field(default_factory=lambda: {"stable": 100.0, "canary": 0.0})
    timestamp: datetime = Field(default_factory=utc_now)
