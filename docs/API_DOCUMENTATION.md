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
  "timestamp": "2026-10-03T05:40:00.000000Z"
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
  "timestamp": "2026-10-03T05:40:00.000000Z",
  "uptime_seconds": 45.12
}
```

### `GET /health/details`
- **Summary**: Detailed Component Diagnostics
- **Description**: Provides sub-system breakdown (FastAPI async engine, Database connectivity parameters, Traffic router engine).
- **Status Code**: `200 OK`

---

## 2. Authentication & Authorization Endpoints (Implemented - Phase 4)

All protected routes require an HTTP Authorization header in the Bearer format:
```text
Authorization: Bearer <access_token>
```

### `POST /auth/register`
- **Summary**: Register New User Account
- **Status Code**: `201 Created`

### `POST /auth/login`
- **Summary**: User Login & JWT Generation
- **Status Code**: `200 OK`

### `GET /auth/me`
- **Summary**: Current Authenticated User Profile
- **Security**: Requires Bearer JWT
- **Status Code**: `200 OK`

### `GET /auth/admin-only`
- **Summary**: RBAC Protected Demo Route (ADMIN only)
- **Status Code**: `200 OK` (Admin) / `403 Forbidden` (User)

---

## 3. Deployment Management Endpoints (Implemented - Phase 5)

All deployment management endpoints require authentication (`Authorization: Bearer <token>`).

### `POST /deployments`
- **Summary**: Create Canary Deployment
- **Description**: Creates a deployment record with baseline Stable (v1) and candidate Canary (v2) versions, and sets initial traffic to `100% Stable / 0% Canary`.
- **Status Code**: `201 Created`
- **Request Body**:
```json
{
  "name": "Payment Gateway Microservice",
  "description": "Canary rollout of optimized checkout engine v2",
  "rollback_threshold": 10.0,
  "evaluation_window_seconds": 60,
  "stable_tag": "v1.0.0",
  "canary_tag": "v2.0.0",
  "stable_latency_ms": 45.0,
  "canary_latency_ms": 48.0,
  "initial_canary_failure_rate": 0.0
}
```
- **Response Example**:
```json
{
  "id": 1,
  "name": "Payment Gateway Microservice",
  "description": "Canary rollout of optimized checkout engine v2",
  "status": "PENDING",
  "rollback_threshold": 10.0,
  "evaluation_window_seconds": 60,
  "user_id": 1,
  "created_at": "2026-10-03T12:00:00.000000Z",
  "updated_at": "2026-10-03T12:00:00.000000Z",
  "versions": [
    {
      "id": 1,
      "deployment_id": 1,
      "version_tag": "v1.0.0",
      "version_type": "STABLE",
      "image_tag": "payment-gateway-microservice:v1.0.0",
      "simulated_latency_ms": 45.0,
      "failure_rate": 0.0,
      "is_active": true,
      "created_at": "2026-10-03T12:00:00.000000Z"
    },
    {
      "id": 2,
      "deployment_id": 1,
      "version_tag": "v2.0.0",
      "version_type": "CANARY",
      "image_tag": "payment-gateway-microservice:v2.0.0",
      "simulated_latency_ms": 48.0,
      "failure_rate": 0.0,
      "is_active": true,
      "created_at": "2026-10-03T12:00:00.000000Z"
    }
  ],
  "traffic_config": {
    "id": 1,
    "deployment_id": 1,
    "stable_percentage": 100.0,
    "canary_percentage": 0.0,
    "last_shifted_at": "2026-10-03T12:00:00.000000Z",
    "updated_at": "2026-10-03T12:00:00.000000Z"
  }
}
```

### `GET /deployments`
- **Summary**: List Deployments
- **Description**: Returns all deployments belonging to the authenticated user (or all deployments if user is an administrator).
- **Status Code**: `200 OK`

### `GET /deployments/{id}`
- **Summary**: Get Deployment Details
- **Description**: Retrieves full deployment state including child version entities and traffic configuration.
- **Status Code**: `200 OK`

### `PUT /deployments/{id}`
- **Summary**: Update Deployment Settings
- **Description**: Modifies mutable parameters such as `rollback_threshold`, `name`, or `description`.
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "rollback_threshold": 12.5,
  "description": "Adjusted threshold for load test"
}
```

### `DELETE /deployments/{id}`
- **Summary**: Delete Deployment
- **Description**: Permanently deletes a deployment with cascading deletion of all associated versions, traffic configs, metrics, and logs.
- **Status Code**: `204 No Content`

### `POST /deployments/{id}/start`
- **Summary**: Start Canary Rollout
- **Description**: Activates deployment by transitioning status from `PENDING` to `RUNNING`.
- **Status Code**: `200 OK`

---

## 4. Planned Endpoints for Subsequent Phases

### Canary Traffic Control & Simulation (Phases 6, 7, 9, 10)
- `POST /deployments/{id}/traffic` - Adjust stable vs canary traffic distribution (e.g., 90/10, 75/25, 50/50, 0/100)
- `POST /deployments/{id}/simulate` - Dispatch simulated requests across traffic split
- `POST /deployments/{id}/failure` - Inject synthetic failure rate into canary version (v2)
- `POST /deployments/{id}/rollback` - Manually trigger rollback to 100% stable

### Observability, Logs & Metrics (Phase 8)
- `GET /deployments/{id}/metrics` - Query real-time metrics (success, error rate, latency)
- `GET /deployments/{id}/logs` - Inspect structured application logs
- `GET /deployments/{id}/history` - View chronological state transitions and rollback events
