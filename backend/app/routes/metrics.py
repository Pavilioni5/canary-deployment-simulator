"""
REST API routes for Metrics, Observability Logs, and Deployment History.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.metrics import (
    DeploymentMetricsSummaryResponse,
    DeploymentLogResponse,
    DeploymentEventResponse
)
from app.services import metrics_service

router = APIRouter(prefix="/deployments", tags=["Metrics & Observability"])


@router.get(
    "/{id}/metrics",
    response_model=DeploymentMetricsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Aggregated Deployment Metrics",
    description="Returns real-time deployment metrics: total requests, stable requests, canary requests, overall/canary/stable error rates, average latency, rollback counts, and time-series snapshots."
)
def get_metrics(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return metrics_service.get_deployment_metrics(
        db=db,
        current_user=current_user,
        deployment_id=id
    )


@router.get(
    "/{id}/logs",
    response_model=List[DeploymentLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Deployment Logs",
    description="Inspects structured diagnostic application logs with optional level and source filtering."
)
def get_logs(
    id: int,
    level: Optional[str] = Query(None, description="Filter by level: INFO, WARNING, ERROR, CRITICAL"),
    source: Optional[str] = Query(None, description="Filter by source: ROUTER, SIMULATOR, MONITOR, SYSTEM, AUTH"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return metrics_service.get_deployment_logs(
        db=db,
        current_user=current_user,
        deployment_id=id,
        level=level,
        source=source,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{id}/history",
    response_model=List[DeploymentEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Deployment Lifecycle Audit History",
    description="Returns chronological audit trail of state transitions: CREATED, STARTED, TRAFFIC_SHIFT, FAILURE_INJECTED, and ROLLBACK events."
)
def get_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return metrics_service.get_deployment_history(
        db=db,
        current_user=current_user,
        deployment_id=id
    )
