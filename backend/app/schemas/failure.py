"""
Pydantic schemas for Controlled Failure Injection & Chaos Engineering.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FailureInjectionRequest(BaseModel):
    failure_rate: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Failure rate to inject (expressed as probability 0.0-1.0 or percentage 0-100, e.g. 0.35 or 35)",
        examples=[0.35]
    )
    error_type: Optional[str] = Field(
        "HTTP_500",
        description="Fault injection profile: HTTP_500, LATENCY_TIMEOUT, DATABASE_ERROR, MEMORY_SPIKE",
        examples=["HTTP_500"]
    )
    affected_version: Optional[str] = Field(
        "CANARY",
        description="Target deployment version for fault injection: CANARY or STABLE",
        examples=["CANARY"]
    )
    latency_ms: Optional[float] = Field(
        None,
        ge=1.0,
        le=10000.0,
        description="Optional simulated latency override in milliseconds",
        examples=[150.0]
    )

    @field_validator("failure_rate")
    @classmethod
    def normalize_failure_rate(cls, v: float) -> float:
        if v > 1.0:
            return round(v / 100.0, 4)
        return round(v, 4)

    @field_validator("affected_version")
    @classmethod
    def validate_affected_version(cls, v: Optional[str]) -> str:
        if not v:
            return "CANARY"
        v_upper = v.upper().strip()
        if v_upper not in ["CANARY", "STABLE"]:
            raise ValueError("affected_version must be either 'CANARY' or 'STABLE'.")
        return v_upper


class FailureInjectionResponse(BaseModel):
    deployment_id: int
    deployment_name: str
    affected_version: str
    version_tag: str
    failure_rate: float
    failure_percentage: float
    error_type: str
    simulated_latency_ms: float
    status: str
    message: str
    timestamp: datetime = Field(default_factory=utc_now)
