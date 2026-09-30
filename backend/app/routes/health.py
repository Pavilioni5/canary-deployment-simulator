"""
System and Health Check API Routes.
"""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.config import settings
from app.schemas.health import (
    SystemInfoResponse,
    HealthCheckResponse,
    DetailedHealthResponse,
    ComponentHealth
)

router = APIRouter(tags=["System & Health"])

# Track service start time for uptime calculation
START_TIME = time.time()


def current_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.get(
    "/",
    response_model=SystemInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="System Information Root",
    description="Returns high-level project metadata, project ID, and API availability status."
)
def get_system_info():
    return SystemInfoResponse(
        project=settings.APP_NAME,
        project_id=settings.PROJECT_ID,
        version="1.0.0",
        status="operational",
        environment=settings.APP_ENV,
        docs_url="/docs",
        timestamp=current_utc()
    )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic Liveness Probe",
    description="Standard health check endpoint suitable for AWS ALB target group health checks and container probes."
)
def get_health_status():
    uptime = round(time.time() - START_TIME, 2)
    return HealthCheckResponse(
        status="healthy",
        environment=settings.APP_ENV,
        timestamp=current_utc(),
        uptime_seconds=uptime
    )


@router.get(
    "/health/details",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed Component Diagnostics",
    description="Inspects the operational health of individual subsystems including API runtime and database connectivity parameters."
)
def get_detailed_health():
    uptime = round(time.time() - START_TIME, 2)
    components = {
        "api": ComponentHealth(
            status="healthy",
            message="FastAPI asynchronous engine is responsive"
        ),
        "database_configured": ComponentHealth(
            status="configured",
            message="Database URL configured",
            details={"driver": settings.DATABASE_URL.split("://")[0]}
        ),
        "traffic_router": ComponentHealth(
            status="ready",
            message="Traffic shifting sub-engine ready for deployment registrations"
        )
    }

    return DetailedHealthResponse(
        status="healthy",
        timestamp=current_utc(),
        uptime_seconds=uptime,
        components=components
    )
