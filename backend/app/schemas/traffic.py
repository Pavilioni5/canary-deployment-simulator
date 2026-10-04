"""
Pydantic schemas for Traffic Shifting and Weighted Traffic Routing Simulation.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.schemas.simulation import SimulatedRequestResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TrafficShiftRequest(BaseModel):
    canary_percentage: float = Field(..., ge=0.0, le=100.0, description="Target percentage for Canary v2 (0.0 to 100.0)", examples=[10.0])
    stable_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Optional target percentage for Stable v1. Defaults to 100 - canary", examples=[90.0])

    @model_validator(mode="after")
    def validate_percentages(self):
        if self.stable_percentage is None:
            self.stable_percentage = round(100.0 - self.canary_percentage, 2)
        else:
            total = round(self.stable_percentage + self.canary_percentage, 2)
            if abs(total - 100.0) > 0.01:
                raise ValueError(f"Sum of stable ({self.stable_percentage}%) and canary ({self.canary_percentage}%) must equal 100.0% (got {total}%).")
        return self


class TrafficShiftResponse(BaseModel):
    deployment_id: int
    stable_percentage: float
    canary_percentage: float
    last_shifted_at: datetime
    message: str


class TrafficSimulationRequest(BaseModel):
    count: int = Field(1, ge=1, le=1000, description="Total number of simulated client requests to dispatch", examples=[50])
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Simulated payload data", examples=[{"route": "/api/v1/checkout", "user_agent": "Mozilla/5.0"}])


class SubsystemMetricsSummary(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float  # Percentage: 0.0 to 100.0
    avg_latency_ms: float


class TrafficSimulationSummaryResponse(BaseModel):
    deployment_id: int
    deployment_name: str
    status: str
    traffic_weights: Dict[str, float]
    total_requests: int
    stable_summary: SubsystemMetricsSummary
    canary_summary: SubsystemMetricsSummary
    overall_summary: SubsystemMetricsSummary
    results: List[SimulatedRequestResult] = []
