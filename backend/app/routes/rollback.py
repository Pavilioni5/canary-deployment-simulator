"""
REST API routes for Manual and Automated Rollback controls.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.rollback import ManualRollbackRequest, RollbackResponse
from app.services import rollback_service

router = APIRouter(prefix="/deployments", tags=["Rollback & Circuit Breaker"])


@router.post(
    "/{id}/rollback",
    response_model=RollbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Manual Deployment Rollback",
    description="Manually trips the circuit breaker: resets traffic immediately to 100% Stable / 0% Canary, transitions status to ROLLED_BACK, and records an audit event."
)
def manual_rollback(
    id: int,
    request: ManualRollbackRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reason = request.reason if request else None
    return rollback_service.execute_manual_rollback(
        db=db,
        current_user=current_user,
        deployment_id=id,
        reason=reason
    )
