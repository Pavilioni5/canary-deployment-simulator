"""
Main FastAPI entry point for Canary Deployment Simulator (P71).
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.deployments import router as deployments_router
from app.routes.simulation import router as simulation_router
from app.routes.traffic import router as traffic_router
from app.routes.metrics import router as metrics_router
from app.routes.rollback import router as rollback_router
from app.database import init_db
from app.utils.init_db import seed_admin_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema and seed default admin on application startup
    init_db()
    seed_admin_user()
    yield


tags_metadata = [
    {
        "name": "System & Health",
        "description": "System availability, operational status, and orchestrator health probes.",
    },
    {
        "name": "Authentication",
        "description": "User registration, JWT token generation, and role-based permissions.",
    },
    {
        "name": "Deployments",
        "description": "Canary deployment lifecycle: creation, traffic shifting, failure injection, and rollbacks.",
    },
    {
        "name": "Simulation & Versions",
        "description": "Stable v1 and Canary v2 execution emulation, synthetic error injection, and latency simulation.",
    },
    {
        "name": "Traffic Routing & Shifting",
        "description": "Weighted traffic shifting algorithm mimicking AWS ALB target group weight distribution.",
    },
    {
        "name": "Rollback & Circuit Breaker",
        "description": "Automated and manual rollback circuit breakers restoring 100% stable traffic upon error breach.",
    },
    {
        "name": "Metrics & Observability",
        "description": "Real-time metrics aggregation, structured application logs, and deployment audit trail.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Cloud-Based Canary Deployment Simulator (P71)

This REST API provides an interactive platform to simulate, control, and monitor **Canary Deployments**.

### Key Architectural Capabilities:
* **Gradual Traffic Shifting**: Dynamically shift traffic from Stable (v1) to Canary (v2).
* **Automated Failure Detection**: Continuous monitoring of error rates against configured thresholds.
* **Circuit-Breaker Automatic Rollback**: Instant reversion to 100% stable if canary breaches health metrics.
* **Enterprise Security**: JWT-based authentication and role-based authorization.
* **Audit Logging & Telemetry**: Full historical audit trail for viva presentation and load verification.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(deployments_router)
app.include_router(simulation_router)
app.include_router(traffic_router)
app.include_router(rollback_router)
app.include_router(metrics_router)
