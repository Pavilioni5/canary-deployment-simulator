"""
Rollback Service: handles automated circuit-breaker rollbacks and manual operator rollbacks.
"""
import json
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.deployment import Deployment, TrafficConfig
from app.models.event import DeploymentEvent
from app.models.log import DeploymentLog
from app.schemas.rollback import RollbackResponse
from app.services.deployment_service import get_deployment_by_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def execute_automatic_rollback(
    db: Session,
    deployment: Deployment,
    canary_error_rate: float,
    canary_count: int,
    canary_failed: int
) -> str:
    """
    Trigger automated circuit breaker rollback when Canary error rate exceeds threshold.
    1. Instantly resets traffic routing to 100% Stable / 0% Canary.
    2. Transitions deployment status to ROLLED_BACK.
    3. Records AUTO_ROLLBACK audit event with full diagnostic details.
    4. Logs CRITICAL alert to application log.
    """
    now = utc_now()
    reason = (
        f"Automatic circuit-breaker rollback triggered: Canary error rate ({canary_error_rate}%) "
        f"exceeded configured failure threshold ({deployment.rollback_threshold}%). "
        f"Traffic instantly restored to 100% Stable (v1)."
    )

    # 1. Reset Traffic Config to 100% Stable / 0% Canary
    config = db.query(TrafficConfig).filter(TrafficConfig.deployment_id == deployment.id).first()
    if config:
        config.stable_percentage = 100.0
        config.canary_percentage = 0.0
        config.last_shifted_at = now

    # 2. Transition Deployment Status
    deployment.status = "ROLLED_BACK"
    deployment.updated_at = now

    # 3. Create Audit Trail Record
    event_details = {
        "trigger": "threshold_exceeded",
        "rollback_threshold": deployment.rollback_threshold,
        "observed_canary_error_rate": canary_error_rate,
        "canary_requests": canary_count,
        "canary_failed": canary_failed,
        "timestamp": now.isoformat()
    }
    event = DeploymentEvent(
        deployment_id=deployment.id,
        event_type="AUTO_ROLLBACK",
        message=reason,
        details=json.dumps(event_details),
        timestamp=now
    )

    # 4. Critical Observability Log
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level="CRITICAL",
        source="CIRCUIT_BREAKER",
        message=f"CIRCUIT BREAKER ACTIVATED: Canary error rate {canary_error_rate}% breached threshold {deployment.rollback_threshold}%. Auto-rollback executed.",
        timestamp=now
    )

    db.add_all([event, log_entry])
    db.commit()
    db.refresh(deployment)
    return reason


def execute_manual_rollback(
    db: Session,
    current_user: User,
    deployment_id: int,
    reason: str = None
) -> RollbackResponse:
    """Manually revert all traffic to 100% Stable v1 and set deployment status to ROLLED_BACK."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    now = utc_now()
    rollback_reason = reason or f"Manual rollback triggered by operator {current_user.email}."

    # 1. Reset Traffic Config
    config = db.query(TrafficConfig).filter(TrafficConfig.deployment_id == deployment.id).first()
    if config:
        config.stable_percentage = 100.0
        config.canary_percentage = 0.0
        config.last_shifted_at = now

    # 2. Update Deployment State
    deployment.status = "ROLLED_BACK"
    deployment.updated_at = now

    # 3. Audit Event
    event = DeploymentEvent(
        deployment_id=deployment.id,
        event_type="MANUAL_ROLLBACK",
        message=rollback_reason,
        details=json.dumps({
            "operator": current_user.email,
            "timestamp": now.isoformat()
        }),
        timestamp=now
    )

    # 4. Structured Log
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level="WARNING",
        source="OPERATOR",
        message=f"Manual rollback executed by {current_user.email}. All traffic reverted to 100% Stable (v1).",
        timestamp=now
    )

    db.add_all([event, log_entry])
    db.commit()
    db.refresh(deployment)

    return RollbackResponse(
        deployment_id=deployment.id,
        deployment_name=deployment.name,
        status="ROLLED_BACK",
        rollback_type="MANUAL",
        reason=rollback_reason,
        rollback_threshold=deployment.rollback_threshold,
        traffic_restored={"stable": 100.0, "canary": 0.0},
        timestamp=now
    )
