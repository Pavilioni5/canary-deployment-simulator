"""
Pydantic schemas for Metrics, Logs, and Deployment History audit trails.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MetricSnapshotResponse(BaseModel):
    id: int
    deployment_id: int
    version_type: str  # "STABLE", "CANARY", "TOTAL"
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time_ms: float
    timestamp: datetime


class DeploymentMetricsSummaryResponse(BaseModel):
    deployment_id: int
    deployment_name: str
    status: str
    rollback_threshold: float
    total_requests: int
    stable_requests: int
    canary_requests: int
    total_successful: int
    total_failed: int
    overall_error_rate: float
    stable_error_rate: float
    canary_error_rate: float
    average_response_time_ms: float
    rollback_count: int
    recent_snapshots: List[MetricSnapshotResponse] = []


class DeploymentLogResponse(BaseModel):
    id: int
    deployment_id: int
    level: str  # INFO, WARNING, ERROR, CRITICAL
    source: str  # ROUTER, SIMULATOR, MONITOR, SYSTEM, AUTH
    message: str
    timestamp: datetime


class DeploymentEventResponse(BaseModel):
    id: int
    deployment_id: int
    event_type: str  # CREATED, STARTED, TRAFFIC_SHIFT, FAILURE_INJECTED, AUTO_ROLLBACK, MANUAL_ROLLBACK, CONFIG_UPDATED
    message: str
    details: Optional[str] = None
    timestamp: datetime
