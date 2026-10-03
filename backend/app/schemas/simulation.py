"""
Pydantic schemas for Stable (v1) and Canary (v2) simulated request execution.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VersionSimulationRequest(BaseModel):
    count: int = Field(1, ge=1, le=1000, description="Number of simulated requests to dispatch", examples=[10])
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Simulated payload data", examples=[{"action": "process_payment", "amount": 99.99}])


class SimulatedRequestResult(BaseModel):
    request_id: str
    version_type: str  # "STABLE" or "CANARY"
    version_tag: str   # "v1.0.0" or "v2.0.0"
    status: str        # "SUCCESS" or "FAILED"
    status_code: int   # 200 or 500
    latency_ms: float
    error_message: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class VersionSimulationSummaryResponse(BaseModel):
    deployment_id: int
    deployment_name: str
    version_type: str
    version_tag: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float  # Percentage: 0.0 to 100.0
    avg_latency_ms: float
    results: List[SimulatedRequestResult] = []


class VersionUpdateConfigRequest(BaseModel):
    simulated_latency_ms: Optional[float] = Field(None, ge=1.0, le=5000.0, description="Base simulated latency in milliseconds", examples=[45.0])
    failure_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of synthetic failure (0.0 to 1.0)", examples=[0.25])
    is_active: Optional[bool] = Field(None, description="Whether this version is active and accepting traffic")
