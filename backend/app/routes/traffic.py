"""
REST API routes for Canary Traffic Shifting and Weighted Traffic Routing Simulation.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.deployment import TrafficConfig
from app.auth.dependencies import get_current_user
from app.schemas.deployment import TrafficConfigResponse
from app.schemas.traffic import (
    TrafficShiftRequest,
    TrafficShiftResponse,
    TrafficSimulationRequest,
    TrafficSimulationSummaryResponse
)
from app.services import traffic_service
from app.services.deployment_service import get_deployment_by_id

router = APIRouter(prefix="/deployments", tags=["Traffic Routing & Shifting"])


@router.post(
    "/{id}/traffic",
    response_model=TrafficShiftResponse,
    status_code=status.HTTP_200_OK,
    summary="Shift Canary Traffic Percentage",
    description="Dynamically adjusts traffic routing percentages between Stable v1 and Canary v2 (e.g., 90/10, 75/25, 50/50, 0/100). Validates total sum is 100% and records an audit event."
)
def configure_traffic(
    id: int,
    request: TrafficShiftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return traffic_service.shift_traffic(
        db=db,
        current_user=current_user,
        deployment_id=id,
        request=request
    )


@router.get(
    "/{id}/traffic",
    response_model=TrafficConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Traffic Split Configuration",
    description="Retrieves the current traffic weights and timestamp of the last shift."
)
def get_traffic_config(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deployment = get_deployment_by_id(db, id, current_user)
    config = db.query(TrafficConfig).filter(TrafficConfig.deployment_id == deployment.id).first()
    return config


@router.post(
    "/{id}/simulate",
    response_model=TrafficSimulationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Client Traffic Across Router",
    description="Dispatches N client requests through the weighted traffic router. Requests are distributed between Stable v1 and Canary v2 in accordance with configured weights."
)
def simulate_traffic(
    id: int,
    request: TrafficSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return traffic_service.simulate_routed_traffic(
        db=db,
        current_user=current_user,
        deployment_id=id,
        count=request.count,
        payload=request.payload
    )
