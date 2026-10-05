"""
Failure Injection & Chaos Engineering Service Engine.
Enables controlled fault injection into Canary or Stable versions to test
observability pipelines and automated circuit breaker rollback triggers.
"""
import json
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.deployment import Deployment, DeploymentVersion
from app.models.event import DeploymentEvent
from app.models.log import DeploymentLog
from app.schemas.failure import FailureInjectionRequest, FailureInjectionResponse
from app.services.deployment_service import get_deployment_by_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def inject_failure(
    db: Session,
    current_user: User,
    deployment_id: int,
    request: FailureInjectionRequest
) -> FailureInjectionResponse:
    """
    Applies synthetic failure rates and fault profiles to a targeted application version.
    Records audit event with event_type='FAILURE_INJECTED' and writes to structured logs.
    """
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    target_type = request.affected_version.upper().strip()

    # Locate version instance
    version = db.query(DeploymentVersion).filter(
        DeploymentVersion.deployment_id == deployment.id,
        DeploymentVersion.version_type == target_type
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{target_type} version not found for deployment ID {deployment_id}."
        )

    # Apply configuration
    error_profile = (request.error_type or "HTTP_500").upper().strip()
    version.failure_rate = request.failure_rate
    version.error_type = error_profile
    if request.latency_ms is not None:
        version.simulated_latency_ms = request.latency_ms

    now = utc_now()
    failure_pct = round(version.failure_rate * 100.0, 2)

    if version.failure_rate > 0.0:
        event_message = (
            f"Controlled failure injected into {version.version_tag} ({version.version_type}): "
            f"failure_rate={failure_pct}%, error_type='{version.error_type}'."
        )
        status_label = "FAILURE_INJECTED"
        log_level = "CRITICAL" if version.failure_rate > 0.5 else "WARNING"
    else:
        event_message = (
            f"Failure injection cleared for {version.version_tag} ({version.version_type}): "
            f"failure_rate reset to 0.0%."
        )
        status_label = "CLEARED"
        log_level = "INFO"

    # Audit Trail Event
    event = DeploymentEvent(
        deployment_id=deployment.id,
        event_type="FAILURE_INJECTED",
        message=event_message,
        details=json.dumps({
            "failure_rate": version.failure_rate,
            "failure_percentage": failure_pct,
            "error_type": version.error_type,
            "affected_version": version.version_type,
            "version_tag": version.version_tag,
            "simulated_latency_ms": version.simulated_latency_ms,
            "operator": current_user.email,
            "timestamp": now.isoformat()
        }),
        timestamp=now
    )

    # Observability Log Entry
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level=log_level,
        source="CHAOS_ENGINE",
        message=(
            f"Chaos fault injection updated by {current_user.email}: "
            f"{version.version_tag} ({version.version_type}) set to {failure_pct}% errors "
            f"[Fault Profile: {version.error_type}, Latency: {version.simulated_latency_ms}ms]."
        ),
        timestamp=now
    )

    db.add_all([event, log_entry])
    db.commit()
    db.refresh(version)

    return FailureInjectionResponse(
        deployment_id=deployment.id,
        deployment_name=deployment.name,
        affected_version=version.version_type,
        version_tag=version.version_tag,
        failure_rate=version.failure_rate,
        failure_percentage=failure_pct,
        error_type=version.error_type,
        simulated_latency_ms=version.simulated_latency_ms,
        status=status_label,
        message=event_message,
        timestamp=now
    )
