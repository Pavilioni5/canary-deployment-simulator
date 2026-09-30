"""
Main FastAPI entry point for Canary Deployment Simulator (P71).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.health import router as health_router

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
        "name": "Metrics & Logs",
        "description": "Real-time metrics, error rate calculations, and structured deployment event logs.",
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
    redoc_url="/redoc"
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
