# API Documentation - Canary Deployment Simulator (P71)

## Overview
This document specifies the REST API endpoints provided by the Canary Deployment Simulator backend built using FastAPI.

## Interactive API Docs
When running locally:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## 1. System & Health Endpoints (Implemented - Phase 2)

### `GET /`
- **Summary**: System Information Root
- **Description**: Returns project metadata, project ID (P71), active version, status, and environment.
- **Status Code**: `200 OK`
- **Response Example**:
```json
{
  "project": "Cloud-Based Canary Deployment Simulator",
  "project_id": "P71",
  "version": "1.0.0",
  "status": "operational",
  "environment": "development",
  "docs_url": "/docs",
  "timestamp": "2026-09-30T16:25:00.000000Z"
}
```

### `GET /health`
- **Summary**: Basic Liveness Probe
- **Description**: Standard health check endpoint for AWS ALB target groups, Docker health checks, and Kubernetes liveness probes.
- **Status Code**: `200 OK`
- **Response Example**:
```json
{
  "status": "healthy",
  "environment": "development",
  "timestamp": "2026-09-30T16:25:00.000000Z",
  "uptime_seconds": 45.12
}
```

### `GET /health/details`
- **Summary**: Detailed Component Diagnostics
- **Description**: Provides sub-system breakdown (FastAPI async engine, Database connectivity parameters, Traffic router engine).
- **Status Code**: `200 OK`
- **Response Example**:
```json
{
  "status": "healthy",
  "timestamp": "2026-09-30T16:25:00.000000Z",
  "uptime_seconds": 45.12,
  "components": {
    "api": {
      "status": "healthy",
      "message": "FastAPI asynchronous engine is responsive",
      "details": null
    },
    "database_configured": {
      "status": "configured",
      "message": "Database URL configured",
      "details": {
        "driver": "sqlite"
      }
    },
    "traffic_router": {
      "status": "ready",
      "message": "Traffic shifting sub-engine ready for deployment registrations",
      "details": null
    }
  }
}
```

---

## 2. Planned Endpoints for Subsequent Phases

### Authentication & Authorization (Phase 4)
- `POST /auth/register` - Register a new user account (Admin/User role)
- `POST /auth/login` - Authenticate credentials and receive JWT access token
- `GET /auth/me` - Retrieve current user profile and permissions

### Deployment Management (Phase 5)
- `POST /deployments` - Create a new deployment with stable (v1) and canary (v2) configs
- `GET /deployments` - List all deployments
- `GET /deployments/{id}` - Retrieve details of a specific deployment
- `POST /deployments/{id}/start` - Launch canary traffic shifting

### Canary Traffic Control & Simulation (Phases 6, 7, 9, 10)
- `POST /deployments/{id}/traffic` - Adjust stable vs canary traffic distribution (e.g., 90/10, 75/25, 50/50, 0/100)
- `POST /deployments/{id}/simulate` - Dispatch simulated requests across traffic split
- `POST /deployments/{id}/failure` - Inject synthetic failure rate into canary version (v2)
- `POST /deployments/{id}/rollback` - Manually trigger rollback to 100% stable

### Observability, Logs & Metrics (Phase 8)
- `GET /deployments/{id}/metrics` - Query real-time metrics (success, error rate, latency)
- `GET /deployments/{id}/logs` - Inspect structured application logs
- `GET /deployments/{id}/history` - View chronological state transitions and rollback events
