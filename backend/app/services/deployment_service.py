"""
Business logic service for Deployment lifecycle and CRUD management.
"""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.deployment import Deployment, DeploymentVersion, TrafficConfig
from app.models.event import DeploymentEvent
from app.models.log import DeploymentLog
from app.schemas.deployment import DeploymentCreateRequest, DeploymentUpdateRequest


def create_deployment(db: Session, current_user: User, data: DeploymentCreateRequest) -> Deployment:
    """Create a new deployment with stable & canary versions, initial traffic config, and audit event."""
    deployment = Deployment(
        name=data.name.strip(),
        description=data.description,
        status="PENDING",
        rollback_threshold=data.rollback_threshold,
        evaluation_window_seconds=data.evaluation_window_seconds,
        user_id=current_user.id
    )
    db.add(deployment)
    db.flush()  # Generates deployment.id

    # 1. Stable Version (v1)
    stable_version = DeploymentVersion(
        deployment_id=deployment.id,
        version_tag=data.stable_tag.strip(),
        version_type="STABLE",
        image_tag=f"{data.name.lower().replace(' ', '-')}:{data.stable_tag.strip()}",
        simulated_latency_ms=data.stable_latency_ms,
        failure_rate=0.0,  # Stable baseline has 0% artificial failures
        is_active=True
    )

    # 2. Canary Version (v2)
    canary_version = DeploymentVersion(
        deployment_id=deployment.id,
        version_tag=data.canary_tag.strip(),
        version_type="CANARY",
        image_tag=f"{data.name.lower().replace(' ', '-')}:{data.canary_tag.strip()}",
        simulated_latency_ms=data.canary_latency_ms,
        failure_rate=data.initial_canary_failure_rate,
        is_active=True
    )

    # 3. Initial Traffic Configuration (100% Stable / 0% Canary)
    traffic_config = TrafficConfig(
        deployment_id=deployment.id,
        stable_percentage=100.0,
        canary_percentage=0.0
    )

    # 4. Lifecycle Audit Event
    initial_event = DeploymentEvent(
        deployment_id=deployment.id,
        event_type="CREATED",
        message=f"Deployment created with Stable ({data.stable_tag}) and Canary ({data.canary_tag}).",
        details=f'{{"threshold": {data.rollback_threshold}, "stable": "{data.stable_tag}", "canary": "{data.canary_tag}"}}'
    )

    # 5. Diagnostic Log
    initial_log = DeploymentLog(
        deployment_id=deployment.id,
        level="INFO",
        source="SYSTEM",
        message=f"Deployment '{deployment.name}' initialized in PENDING state by {current_user.email}."
    )

    db.add_all([stable_version, canary_version, traffic_config, initial_event, initial_log])
    db.commit()
    db.refresh(deployment)
    return deployment


def get_deployments(db: Session, current_user: User, skip: int = 0, limit: int = 50) -> List[Deployment]:
    """Retrieve list of deployments. Admins see all; standard users see their own."""
    query = db.query(Deployment)
    if current_user.role != "ADMIN":
        query = query.filter(Deployment.user_id == current_user.id)
    return query.order_by(Deployment.created_at.desc()).offset(skip).limit(limit).all()


def get_deployment_by_id(db: Session, deployment_id: int, current_user: User) -> Deployment:
    """Retrieve specific deployment by ID with authorization verification."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment with ID {deployment_id} not found."
        )
    if current_user.role != "ADMIN" and deployment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to view this deployment."
        )
    return deployment


def update_deployment(db: Session, deployment_id: int, current_user: User, data: DeploymentUpdateRequest) -> Deployment:
    """Update editable parameters of a deployment."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    
    if data.name is not None:
        deployment.name = data.name.strip()
    if data.description is not None:
        deployment.description = data.description
    if data.rollback_threshold is not None:
        old_threshold = deployment.rollback_threshold
        deployment.rollback_threshold = data.rollback_threshold
        
        event = DeploymentEvent(
            deployment_id=deployment.id,
            event_type="CONFIG_UPDATED",
            message=f"Rollback threshold changed from {old_threshold}% to {data.rollback_threshold}%.",
            details=f'{{"old": {old_threshold}, "new": {data.rollback_threshold}}}'
        )
        db.add(event)
    if data.evaluation_window_seconds is not None:
        deployment.evaluation_window_seconds = data.evaluation_window_seconds

    db.commit()
    db.refresh(deployment)
    return deployment


def delete_deployment(db: Session, deployment_id: int, current_user: User) -> None:
    """Delete a deployment and cascade cleanup all child versions, traffic, metrics, and logs."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    db.delete(deployment)
    db.commit()


def start_deployment(db: Session, deployment_id: int, current_user: User) -> Deployment:
    """Transition deployment state from PENDING to RUNNING to enable traffic simulation."""
    deployment = get_deployment_by_id(db, deployment_id, current_user)
    
    if deployment.status == "RUNNING":
        return deployment
    if deployment.status == "ROLLED_BACK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start a rolled-back deployment directly. Please adjust configuration or create a new rollout."
        )
    
    deployment.status = "RUNNING"
    event = DeploymentEvent(
        deployment_id=deployment.id,
        event_type="STARTED",
        message="Canary rollout lifecycle activated. State transitioned to RUNNING.",
        details='{"status": "RUNNING"}'
    )
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level="INFO",
        source="CONTROLLER",
        message="Canary deployment started and ready to route simulated traffic."
    )
    db.add_all([event, log_entry])
    db.commit()
    db.refresh(deployment)
    return deployment
