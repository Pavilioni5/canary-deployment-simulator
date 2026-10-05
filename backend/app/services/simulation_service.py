"""
Service engine simulating runtime execution for Stable (v1) and Canary (v2) instances.
Simulates latency, network jitter, cloud ALB headers, and configurable failure conditions.
"""
import random
import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.deployment import Deployment, DeploymentVersion
from app.models.log import DeploymentLog
from app.schemas.simulation import (
    SimulatedRequestResult,
    VersionSimulationSummaryResponse,
    VersionUpdateConfigRequest
)
from app.services.deployment_service import get_deployment_by_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def execute_single_version_request(
    version: DeploymentVersion,
    payload: Dict[str, Any] = None
) -> SimulatedRequestResult:
    """Execute a single simulated request against an application version instance."""
    # Simulate network latency with realistic +/- 10% jitter
    base_latency = version.simulated_latency_ms or 50.0
    jitter = random.uniform(-base_latency * 0.1, base_latency * 0.1)
    latency_ms = max(1.0, round(base_latency + jitter, 2))

    # Generate synthetic AWS Application Load Balancer trace ID
    trace_id = f"Root=1-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:24]}"
    req_id = f"req-{uuid.uuid4().hex[:12]}"

    headers = {
        "X-Request-Id": req_id,
        "X-Amzn-Trace-Id": trace_id,
        "X-App-Version": version.version_tag,
        "X-Target-Group": f"tg-{version.version_type.lower()}",
        "X-Simulated-Latency": f"{latency_ms}ms"
    }

    # Evaluate artificial failure probability
    is_failed = random.random() < version.failure_rate

    if is_failed:
        error_type = (getattr(version, "error_type", None) or "HTTP_500").upper().strip()
        status_code = 500
        error_msg = f"Simulated HTTP 500: Internal server fault injected in {version.version_tag} ({version.version_type})"

        if error_type in ["LATENCY_TIMEOUT", "TIMEOUT"]:
            status_code = 504
            latency_ms = max(latency_ms, 2500.0)
            error_msg = f"Simulated HTTP 504: Gateway timeout injected in {version.version_tag} ({version.version_type})"
        elif error_type in ["DATABASE_ERROR", "DB_CONNECTION_DROP"]:
            status_code = 500
            error_msg = f"Simulated DatabaseConnectionError: Connection pool exhausted in {version.version_tag} ({version.version_type})"
        elif error_type in ["MEMORY_SPIKE", "OUT_OF_MEMORY", "MEMORY_PRESSURE"]:
            status_code = 503
            error_msg = f"Simulated HTTP 503: Service Unavailable due to memory pressure in {version.version_tag} ({version.version_type})"
        elif error_type not in ["HTTP_500", "INTERNAL_SERVER_ERROR"]:
            error_msg = f"Simulated Fault ({error_type}): Error injected in {version.version_tag} ({version.version_type})"

        headers["X-Fault-Injected"] = error_type
        headers["X-Simulated-Latency"] = f"{latency_ms}ms"

        return SimulatedRequestResult(
            request_id=req_id,
            version_type=version.version_type,
            version_tag=version.version_tag,
            status="FAILED",
            status_code=status_code,
            latency_ms=latency_ms,
            error_message=error_msg,
            headers=headers,
            timestamp=utc_now()
        )
    else:
        return SimulatedRequestResult(
            request_id=req_id,
            version_type=version.version_type,
            version_tag=version.version_tag,
            status="SUCCESS",
            status_code=200,
            latency_ms=latency_ms,
            error_message=None,
            headers=headers,
            timestamp=utc_now()
        )


def simulate_version_batch(
    db: Session,
    current_user: User,
    deployment_id: int,
    version_type: str,
    count: int = 1,
    payload: Dict[str, Any] = None
) -> VersionSimulationSummaryResponse:
    """Dispatch a batch of simulated requests directly to a target version (STABLE or CANARY)."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    
    target_type = version_type.upper().strip()
    if target_type not in ["STABLE", "CANARY"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid version_type '{version_type}'. Allowed values: 'STABLE' or 'CANARY'."
        )

    # Locate version entity
    version = db.query(DeploymentVersion).filter(
        DeploymentVersion.deployment_id == deployment.id,
        DeploymentVersion.version_type == target_type
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{target_type} version not found for deployment ID {deployment_id}."
        )

    if not version.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{target_type} version ({version.version_tag}) is inactive and cannot receive traffic."
        )

    # Execute simulation loop
    results: List[SimulatedRequestResult] = []
    total_latency = 0.0
    successful_count = 0
    failed_count = 0

    for _ in range(count):
        res = execute_single_version_request(version, payload)
        results.append(res)
        total_latency += res.latency_ms
        if res.status == "SUCCESS":
            successful_count += 1
        else:
            failed_count += 1

    avg_latency = round(total_latency / count, 2) if count > 0 else 0.0
    error_rate = round((failed_count / count) * 100.0, 2) if count > 0 else 0.0

    # Write diagnostic log entry
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level="INFO" if error_rate == 0 else ("WARNING" if error_rate < 50 else "ERROR"),
        source="SIMULATOR",
        message=f"Simulated {count} requests to {version.version_tag} ({target_type}). Success: {successful_count}, Failed: {failed_count}, Error Rate: {error_rate}%, Avg Latency: {avg_latency}ms."
    )
    db.add(log_entry)
    db.commit()

    return VersionSimulationSummaryResponse(
        deployment_id=deployment.id,
        deployment_name=deployment.name,
        version_type=version.version_type,
        version_tag=version.version_tag,
        total_requests=count,
        successful_requests=successful_count,
        failed_requests=failed_count,
        error_rate=error_rate,
        avg_latency_ms=avg_latency,
        results=results
    )


def update_version_config(
    db: Session,
    current_user: User,
    deployment_id: int,
    version_type: str,
    config: VersionUpdateConfigRequest
) -> DeploymentVersion:
    """Modify simulation parameters (latency, failure rate, active status) of an application version."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    
    target_type = version_type.upper().strip()
    version = db.query(DeploymentVersion).filter(
        DeploymentVersion.deployment_id == deployment.id,
        DeploymentVersion.version_type == target_type
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{target_type} version not found for deployment {deployment_id}."
        )

    changes = []
    if config.simulated_latency_ms is not None:
        version.simulated_latency_ms = config.simulated_latency_ms
        changes.append(f"latency={config.simulated_latency_ms}ms")
    if config.failure_rate is not None:
        version.failure_rate = config.failure_rate
        changes.append(f"failure_rate={config.failure_rate * 100.0}%")
    if config.is_active is not None:
        version.is_active = config.is_active
        changes.append(f"active={config.is_active}")

    if changes:
        log_entry = DeploymentLog(
            deployment_id=deployment.id,
            level="INFO",
            source="CONFIG",
            message=f"Updated {target_type} ({version.version_tag}) configuration: {', '.join(changes)}."
        )
        db.add(log_entry)

    db.commit()
    db.refresh(version)
    return version
