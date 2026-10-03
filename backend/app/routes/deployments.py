"""
REST API routes for Canary Deployment CRUD and lifecycle management.
"""
from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.deployment import (
    DeploymentCreateRequest,
    DeploymentUpdateRequest,
    DeploymentResponse,
    DeploymentDetailResponse
)
from app.services import deployment_service

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.post(
    "",
    response_model=DeploymentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Canary Deployment",
    description="Initializes a new deployment with stable (v1) and canary (v2) version records and default 100/0 traffic split."
)
def create_new_deployment(
    request: DeploymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return deployment_service.create_deployment(db, current_user, request)


@router.get(
    "",
    response_model=List[DeploymentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Deployments",
    description="Retrieves deployments. Standard users see their own; administrators see all deployments across the system."
)
def list_deployments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return deployment_service.get_deployments(db, current_user, skip=skip, limit=limit)


@router.get(
    "/{id}",
    response_model=DeploymentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Deployment Details",
    description="Returns detailed information for a specific deployment including versions, current traffic split, and status."
)
def get_deployment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return deployment_service.get_deployment_by_id(db, id, current_user)


@router.put(
    "/{id}",
    response_model=DeploymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Deployment Settings",
    description="Updates editable attributes such as rollback threshold or deployment description."
)
def update_deployment(
    id: int,
    request: DeploymentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return deployment_service.update_deployment(db, id, current_user, request)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Deployment",
    description="Deletes a deployment and permanently cascades deletions to all associated versions, metrics, and logs."
)
def delete_deployment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deployment_service.delete_deployment(db, id, current_user)
    return None


@router.post(
    "/{id}/start",
    response_model=DeploymentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Start Canary Rollout",
    description="Activates the deployment, transitioning its status from PENDING to RUNNING to enable traffic simulation."
)
def start_deployment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return deployment_service.start_deployment(db, id, current_user)
