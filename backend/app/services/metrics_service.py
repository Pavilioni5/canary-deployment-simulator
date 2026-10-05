"""
Service for computing, querying, and persisting Metrics, Logs, and Deployment History.
"""
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.deployment import Deployment
from app.models.metric import Metric
from app.models.event import DeploymentEvent
from app.models.log import DeploymentLog
from app.schemas.metrics import (
    DeploymentMetricsSummaryResponse,
    MetricSnapshotResponse,
    DeploymentLogResponse,
    DeploymentEventResponse
)
from app.schemas.traffic import SubsystemMetricsSummary
from app.services.deployment_service import get_deployment_by_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def record_simulation_metrics(
    db: Session,
    deployment_id: int,
    stable_summary: SubsystemMetricsSummary,
    canary_summary: SubsystemMetricsSummary,
    overall_summary: SubsystemMetricsSummary
) -> None:
    """Persist metric snapshots for STABLE, CANARY, and TOTAL target groups."""
    now = utc_now()

    records = [
        Metric(
            deployment_id=deployment_id,
            version_type="STABLE",
            total_requests=stable_summary.total_requests,
            successful_requests=stable_summary.successful_requests,
            failed_requests=stable_summary.failed_requests,
            error_rate=stable_summary.error_rate,
            avg_response_time_ms=stable_summary.avg_latency_ms,
            timestamp=now
        ),
        Metric(
            deployment_id=deployment_id,
            version_type="CANARY",
            total_requests=canary_summary.total_requests,
            successful_requests=canary_summary.successful_requests,
            failed_requests=canary_summary.failed_requests,
            error_rate=canary_summary.error_rate,
            avg_response_time_ms=canary_summary.avg_latency_ms,
            timestamp=now
        ),
        Metric(
            deployment_id=deployment_id,
            version_type="TOTAL",
            total_requests=overall_summary.total_requests,
            successful_requests=overall_summary.successful_requests,
            failed_requests=overall_summary.failed_requests,
            error_rate=overall_summary.error_rate,
            avg_response_time_ms=overall_summary.avg_latency_ms,
            timestamp=now
        )
    ]
    db.add_all(records)
    db.commit()


def get_deployment_metrics(
    db: Session,
    current_user: User,
    deployment_id: int
) -> DeploymentMetricsSummaryResponse:
    """
    Compute aggregate metrics across all simulation runs for a deployment:
    - total_requests
    - stable_requests
    - canary_requests
    - error_rate (overall, canary, stable)
    - average_response_time_ms
    - rollback_count
    - recent time-series snapshots
    """
    deployment = get_deployment_by_id(db, deployment_id, current_user)

    # 1. Aggregate Stable metrics
    stable_stats = db.query(
        func.coalesce(func.sum(Metric.total_requests), 0).label("total"),
        func.coalesce(func.sum(Metric.successful_requests), 0).label("success"),
        func.coalesce(func.sum(Metric.failed_requests), 0).label("failed")
    ).filter(
        Metric.deployment_id == deployment.id,
        Metric.version_type == "STABLE"
    ).first()

    # 2. Aggregate Canary metrics
    canary_stats = db.query(
        func.coalesce(func.sum(Metric.total_requests), 0).label("total"),
        func.coalesce(func.sum(Metric.successful_requests), 0).label("success"),
        func.coalesce(func.sum(Metric.failed_requests), 0).label("failed")
    ).filter(
        Metric.deployment_id == deployment.id,
        Metric.version_type == "CANARY"
    ).first()

    # 3. Overall Totals
    stable_reqs = int(stable_stats.total)
    stable_failed = int(stable_stats.failed)
    stable_success = int(stable_stats.success)

    canary_reqs = int(canary_stats.total)
    canary_failed = int(canary_stats.failed)
    canary_success = int(canary_stats.success)

    total_requests = stable_reqs + canary_reqs
    total_failed = stable_failed + canary_failed
    total_successful = stable_success + canary_success

    overall_error_rate = round((total_failed / total_requests) * 100.0, 2) if total_requests > 0 else 0.0
    stable_error_rate = round((stable_failed / stable_reqs) * 100.0, 2) if stable_reqs > 0 else 0.0
    canary_error_rate = round((canary_failed / canary_reqs) * 100.0, 2) if canary_reqs > 0 else 0.0

    # 4. Average response time across TOTAL metric snapshots
    avg_latency_query = db.query(
        func.coalesce(func.avg(Metric.avg_response_time_ms), 0.0)
    ).filter(
        Metric.deployment_id == deployment.id,
        Metric.version_type == "TOTAL"
    ).scalar()
    avg_latency = round(float(avg_latency_query), 2)

    # 5. Rollback incidents count
    rollback_count = db.query(DeploymentEvent).filter(
        DeploymentEvent.deployment_id == deployment.id,
        DeploymentEvent.event_type.in_(["AUTO_ROLLBACK", "MANUAL_ROLLBACK"])
    ).count()

    # 6. Recent 30 snapshots for charts
    snapshots = db.query(Metric).filter(
        Metric.deployment_id == deployment.id
    ).order_by(Metric.timestamp.desc()).limit(30).all()

    snapshot_responses = [
        MetricSnapshotResponse(
            id=s.id,
            deployment_id=s.deployment_id,
            version_type=s.version_type,
            total_requests=s.total_requests,
            successful_requests=s.successful_requests,
            failed_requests=s.failed_requests,
            error_rate=s.error_rate,
            avg_response_time_ms=s.avg_response_time_ms,
            timestamp=s.timestamp
        )
        for s in reversed(snapshots)
    ]

    return DeploymentMetricsSummaryResponse(
        deployment_id=deployment.id,
        deployment_name=deployment.name,
        status=deployment.status,
        rollback_threshold=deployment.rollback_threshold,
        total_requests=total_requests,
        stable_requests=stable_reqs,
        canary_requests=canary_reqs,
        total_successful=total_successful,
        total_failed=total_failed,
        overall_error_rate=overall_error_rate,
        stable_error_rate=stable_error_rate,
        canary_error_rate=canary_error_rate,
        average_response_time_ms=avg_latency,
        rollback_count=rollback_count,
        recent_snapshots=snapshot_responses
    )


def get_deployment_logs(
    db: Session,
    current_user: User,
    deployment_id: int,
    level: Optional[str] = None,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[DeploymentLogResponse]:
    """Retrieve structured diagnostic application logs with optional level/source filters."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    query = db.query(DeploymentLog).filter(DeploymentLog.deployment_id == deployment.id)

    if level:
        query = query.filter(DeploymentLog.level == level.upper().strip())
    if source:
        query = query.filter(DeploymentLog.source == source.upper().strip())

    logs = query.order_by(DeploymentLog.timestamp.desc()).offset(skip).limit(limit).all()

    return [
        DeploymentLogResponse(
            id=l.id,
            deployment_id=l.deployment_id,
            level=l.level,
            source=l.source,
            message=l.message,
            timestamp=l.timestamp
        )
        for l in logs
    ]


def get_deployment_history(
    db: Session,
    current_user: User,
    deployment_id: int
) -> List[DeploymentEventResponse]:
    """Retrieve chronological audit trail of deployment state transitions and events."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    events = db.query(DeploymentEvent).filter(
        DeploymentEvent.deployment_id == deployment.id
    ).order_by(DeploymentEvent.timestamp.desc()).all()

    return [
        DeploymentEventResponse(
            id=e.id,
            deployment_id=e.deployment_id,
            event_type=e.event_type,
            message=e.message,
            details=e.details,
            timestamp=e.timestamp
        )
        for e in events
    ]
