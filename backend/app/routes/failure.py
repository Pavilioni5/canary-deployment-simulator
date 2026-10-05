"""
REST API routes for Controlled Failure Injection & Chaos Engineering.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.failure import FailureInjectionRequest, FailureInjectionResponse
from app.services import failure_service

router = APIRouter(prefix="/deployments", tags=["Controlled Failure Injection"])


@router.post(
    "/{id}/failure",
    response_model=FailureInjectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Inject Controlled Failure",
    description="Configures synthetic fault injection (error rate, error type, and latency) into a target version (default CANARY) to evaluate monitoring and circuit breaker triggers."
)
def inject_failure_endpoint(
    id: int,
    request: FailureInjectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return failure_service.inject_failure(
        db=db,
        current_user=current_user,
        deployment_id=id,
        request=request
    )


@router.delete(
    "/{id}/failure",
    response_model=FailureInjectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear Failure Injection",
    description="Resets the synthetic failure rate on the Canary version to 0.0%, clearing all active chaos fault profiles."
)
def clear_failure_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reset_request = FailureInjectionRequest(
        failure_rate=0.0,
        error_type="HTTP_500",
        affected_version="CANARY"
    )
    return failure_service.inject_failure(
        db=db,
        current_user=current_user,
        deployment_id=id,
        request=reset_request
    )
