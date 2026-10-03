"""
REST API routes for Stable (v1) and Canary (v2) simulated request execution.
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.deployment import DeploymentVersionResponse
from app.schemas.simulation import (
    VersionSimulationRequest,
    VersionSimulationSummaryResponse,
    VersionUpdateConfigRequest
)
from app.services import simulation_service
from app.services.deployment_service import get_deployment_by_id

router = APIRouter(prefix="/deployments", tags=["Simulation & Versions"])


@router.post(
    "/{id}/simulate/version/{version_type}",
    response_model=VersionSimulationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Requests to Specific Version",
    description="Dispatches simulated requests directly to either the Stable (v1) or Canary (v2) version to evaluate latency and error injection."
)
def simulate_version_traffic(
    id: int,
    version_type: str,
    request: VersionSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return simulation_service.simulate_version_batch(
        db=db,
        current_user=current_user,
        deployment_id=id,
        version_type=version_type,
        count=request.count,
        payload=request.payload
    )


@router.get(
    "/{id}/versions",
    response_model=List[DeploymentVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Deployment Versions",
    description="Lists the active version instances (Stable v1 and Canary v2) with their latency, image tag, and failure parameters."
)
def get_deployment_versions(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deployment = get_deployment_by_id(db, id, current_user)
    return deployment.versions


@router.put(
    "/{id}/versions/{version_type}",
    response_model=DeploymentVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Configure Version Simulation Parameters",
    description="Updates simulated latency, synthetic failure rate, or active status for a specific version (STABLE or CANARY)."
)
def update_version_parameters(
    id: int,
    version_type: str,
    request: VersionUpdateConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return simulation_service.update_version_config(
        db=db,
        current_user=current_user,
        deployment_id=id,
        version_type=version_type,
        config=request
    )
