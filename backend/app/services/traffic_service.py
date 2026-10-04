"""
Traffic Routing and Shifting Service Engine.
Implements dynamic weighted routing algorithm mimicking AWS Application Load Balancers.
"""
import random
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.deployment import Deployment, DeploymentVersion, TrafficConfig
from app.models.event import DeploymentEvent
from app.models.log import DeploymentLog
from app.schemas.traffic import (
    TrafficShiftRequest,
    TrafficShiftResponse,
    TrafficSimulationSummaryResponse,
    SubsystemMetricsSummary
)
from app.schemas.simulation import SimulatedRequestResult
from app.services.deployment_service import get_deployment_by_id
from app.services.simulation_service import execute_single_version_request


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def shift_traffic(
    db: Session,
    current_user: User,
    deployment_id: int,
    request: TrafficShiftRequest
) -> TrafficShiftResponse:
    """Adjust traffic split percentages between Stable (v1) and Canary (v2)."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)

    if deployment.status == "ROLLED_BACK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot alter traffic on a ROLLED_BACK deployment. Please create a new deployment or restart."
        )

    config = db.query(TrafficConfig).filter(TrafficConfig.deployment_id == deployment.id).first()
    if not config:
        config = TrafficConfig(
            deployment_id=deployment.id,
            stable_percentage=request.stable_percentage,
            canary_percentage=request.canary_percentage,
            last_shifted_at=utc_now()
        )
        db.add(config)
    else:
        old_stable = config.stable_percentage
        old_canary = config.canary_percentage
        config.stable_percentage = request.stable_percentage
        config.canary_percentage = request.canary_percentage
        config.last_shifted_at = utc_now()

    # Create audit event
    event = DeploymentEvent(
        deployment_id=deployment.id,
        event_type="TRAFFIC_SHIFT",
        message=f"Traffic shifted: Stable {request.stable_percentage}% / Canary {request.canary_percentage}%.",
        details=f'{{"stable": {request.stable_percentage}, "canary": {request.canary_percentage}}}'
    )

    # Append diagnostic log
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level="INFO",
        source="ROUTER",
        message=f"Weighted target group adjusted by {current_user.email}: Stable={request.stable_percentage}%, Canary={request.canary_percentage}%."
    )

    db.add_all([event, log_entry])
    db.commit()
    db.refresh(config)

    return TrafficShiftResponse(
        deployment_id=deployment.id,
        stable_percentage=config.stable_percentage,
        canary_percentage=config.canary_percentage,
        last_shifted_at=config.last_shifted_at,
        message=f"Traffic weights successfully updated to {config.stable_percentage}% Stable / {config.canary_percentage}% Canary."
    )


def select_target_version(
    canary_percentage: float,
    stable_version: DeploymentVersion,
    canary_version: DeploymentVersion
) -> Tuple[DeploymentVersion, str]:
    """
    Weighted random selection algorithm mimicking AWS ALB weighted target groups.
    Rolls a pseudo-random float r in [0.0, 100.0). If r < canary_percentage, targets Canary.
    """
    if canary_percentage <= 0.0:
        return stable_version, "STABLE"
    if canary_percentage >= 100.0:
        return canary_version, "CANARY"

    roll = random.uniform(0.0, 100.0)
    if roll < canary_percentage:
        return (canary_version, "CANARY") if canary_version.is_active else (stable_version, "STABLE")
    else:
        return (stable_version, "STABLE") if stable_version.is_active else (canary_version, "CANARY")


def simulate_routed_traffic(
    db: Session,
    current_user: User,
    deployment_id: int,
    count: int = 1,
    payload: Dict[str, Any] = None
) -> TrafficSimulationSummaryResponse:
    """
    Dispatch client requests through the weighted traffic router.
    Routes requests according to active stable/canary weights, executing version behavior.
    """
    deployment = get_deployment_by_id(db, deployment_id, current_user)

    if deployment.status != "RUNNING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Traffic simulation requires deployment status 'RUNNING' (current status: '{deployment.status}'). Please start deployment first."
        )

    config = db.query(TrafficConfig).filter(TrafficConfig.deployment_id == deployment.id).first()
    if not config:
        config = TrafficConfig(deployment_id=deployment.id, stable_percentage=100.0, canary_percentage=0.0)
        db.add(config)
        db.commit()

    stable_version = db.query(DeploymentVersion).filter(
        DeploymentVersion.deployment_id == deployment.id,
        DeploymentVersion.version_type == "STABLE"
    ).first()

    canary_version = db.query(DeploymentVersion).filter(
        DeploymentVersion.deployment_id == deployment.id,
        DeploymentVersion.version_type == "CANARY"
    ).first()

    if not stable_version or not canary_version:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deployment versions are improperly configured. Both STABLE and CANARY instances must exist."
        )

    results: List[SimulatedRequestResult] = []

    # Counters
    stable_count = 0
    stable_success = 0
    stable_failed = 0
    stable_latencies = []

    canary_count = 0
    canary_success = 0
    canary_failed = 0
    canary_latencies = []

    for _ in range(count):
        target_version, route_choice = select_target_version(
            config.canary_percentage,
            stable_version,
            canary_version
        )
        res = execute_single_version_request(target_version, payload)
        
        # Inject ALB routing metadata headers
        res.headers["X-Canary-Routing"] = route_choice.lower()
        res.headers["X-Configured-Canary-Weight"] = f"{config.canary_percentage}%"
        res.headers["X-Configured-Stable-Weight"] = f"{config.stable_percentage}%"
        
        results.append(res)

        if route_choice == "CANARY":
            canary_count += 1
            canary_latencies.append(res.latency_ms)
            if res.status == "SUCCESS":
                canary_success += 1
            else:
                canary_failed += 1
        else:
            stable_count += 1
            stable_latencies.append(res.latency_ms)
            if res.status == "SUCCESS":
                stable_success += 1
            else:
                stable_failed += 1

    # Metrics compilation
    stable_summary = SubsystemMetricsSummary(
        total_requests=stable_count,
        successful_requests=stable_success,
        failed_requests=stable_failed,
        error_rate=round((stable_failed / stable_count) * 100.0, 2) if stable_count > 0 else 0.0,
        avg_latency_ms=round(sum(stable_latencies) / stable_count, 2) if stable_count > 0 else 0.0
    )

    canary_summary = SubsystemMetricsSummary(
        total_requests=canary_count,
        successful_requests=canary_success,
        failed_requests=canary_failed,
        error_rate=round((canary_failed / canary_count) * 100.0, 2) if canary_count > 0 else 0.0,
        avg_latency_ms=round(sum(canary_latencies) / canary_count, 2) if canary_count > 0 else 0.0
    )

    total_failed = stable_failed + canary_failed
    total_successful = stable_success + canary_success
    all_latencies = stable_latencies + canary_latencies
    overall_summary = SubsystemMetricsSummary(
        total_requests=count,
        successful_requests=total_successful,
        failed_requests=total_failed,
        error_rate=round((total_failed / count) * 100.0, 2) if count > 0 else 0.0,
        avg_latency_ms=round(sum(all_latencies) / count, 2) if count > 0 else 0.0
    )

    # Diagnostic execution log
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level="INFO" if total_failed == 0 else "WARNING",
        source="ROUTER",
        message=f"Traffic simulation: {count} requests dispatched across split (Stable: {stable_count}, Canary: {canary_count}). Overall error rate: {overall_summary.error_rate}%."
    )
    db.add(log_entry)
    db.commit()

    return TrafficSimulationSummaryResponse(
        deployment_id=deployment.id,
        deployment_name=deployment.name,
        status=deployment.status,
        traffic_weights={
            "stable": config.stable_percentage,
            "canary": config.canary_percentage
        },
        total_requests=count,
        stable_summary=stable_summary,
        canary_summary=canary_summary,
        overall_summary=overall_summary,
        results=results
    )
