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

### `GET /health`
- **Summary**: Basic Liveness Probe
- **Description**: Standard health check endpoint for AWS ALB target groups, Docker health checks, and Kubernetes liveness probes.
- **Status Code**: `200 OK`

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

### `POST /deployments`
- **Summary**: Create Canary Deployment
- **Description**: Creates a deployment record with baseline Stable (v1) and candidate Canary (v2) versions, and sets initial traffic to `100% Stable / 0% Canary`.
- **Status Code**: `201 Created`

### `GET /deployments`
- **Summary**: List Deployments
- **Status Code**: `200 OK`

### `GET /deployments/{id}`
- **Summary**: Get Deployment Details
- **Status Code**: `200 OK`

### `PUT /deployments/{id}`
- **Summary**: Update Deployment Settings
- **Status Code**: `200 OK`

### `DELETE /deployments/{id}`
- **Summary**: Delete Deployment
- **Status Code**: `204 No Content`

### `POST /deployments/{id}/start`
- **Summary**: Start Canary Rollout
- **Description**: Activates deployment by transitioning status from `PENDING` to `RUNNING`.
- **Status Code**: `200 OK`

---

## 4. Version Simulation Endpoints (Implemented - Phase 6)

### `POST /deployments/{id}/simulate/version/{version_type}`
- **Summary**: Simulate Requests Directly to Target Version (STABLE or CANARY)
- **Status Code**: `200 OK`

### `GET /deployments/{id}/versions`
- **Summary**: Get Deployment Versions
- **Status Code**: `200 OK`

### `PUT /deployments/{id}/versions/{version_type}`
- **Summary**: Configure Version Simulation Parameters (Latency, Failure Rate)
- **Status Code**: `200 OK`

---

## 5. Traffic Routing & Shifting Endpoints (Implemented - Phase 7)

### `POST /deployments/{id}/traffic`
- **Summary**: Shift Canary Traffic Percentage
- **Description**: Dynamically configures traffic routing weights between Stable v1 and Canary v2 (e.g. 90/10, 75/25, 50/50, 0/100).
- **Status Code**: `200 OK`

### `GET /deployments/{id}/traffic`
- **Summary**: Get Current Traffic Split Configuration
- **Status Code**: `200 OK`

### `POST /deployments/{id}/simulate`
- **Summary**: Simulate Client Traffic Across Weighted Router
- **Description**: Dispatches N client requests through the weighted traffic router and persists metric snapshots.
- **Status Code**: `200 OK`

---

## 6. Metrics & Observability Endpoints (Implemented - Phase 8)

All observability endpoints require authentication (`Authorization: Bearer <token>`).

### `GET /deployments/{id}/metrics`
- **Summary**: Get Aggregated Deployment Metrics
- **Description**: Returns real-time metrics computed across historical simulations: total requests, stable requests, canary requests, overall/canary/stable error rates, average latency, rollback counts, and time-series snapshots for chart rendering.
- **Status Code**: `200 OK`
- **Response Example**:
```json
{
  "deployment_id": 1,
  "deployment_name": "Checkout Microservice",
  "status": "RUNNING",
  "rollback_threshold": 10.0,
  "total_requests": 150,
  "stable_requests": 112,
  "canary_requests": 38,
  "total_successful": 147,
  "total_failed": 3,
  "overall_error_rate": 2.0,
  "stable_error_rate": 0.0,
  "canary_error_rate": 7.89,
  "average_response_time_ms": 28.45,
  "rollback_count": 0,
  "recent_snapshots": [
    {
      "id": 1,
      "deployment_id": 1,
      "version_type": "TOTAL",
      "total_requests": 50,
      "successful_requests": 49,
      "failed_requests": 1,
      "error_rate": 2.0,
      "avg_response_time_ms": 28.1,
      "timestamp": "2026-10-05T09:40:00.000000Z"
    }
  ]
}
```

### `GET /deployments/{id}/logs`
- **Summary**: Get Deployment Application Logs
- **Description**: Inspects structured diagnostic logs. Supports optional filtering by `level` (INFO, WARNING, ERROR, CRITICAL) and `source` (ROUTER, SIMULATOR, MONITOR, SYSTEM, AUTH), with pagination.
- **Query Parameters**:
  - `level`: e.g. `ERROR`
  - `source`: e.g. `ROUTER`
  - `skip`: default `0`
  - `limit`: default `50`
- **Status Code**: `200 OK`
- **Response Example**:
```json
[
  {
    "id": 10,
    "deployment_id": 1,
    "level": "INFO",
    "source": "ROUTER",
    "message": "Traffic simulation: 50 requests dispatched across split (Stable: 38, Canary: 12). Overall error rate: 0.0%.",
    "timestamp": "2026-10-05T09:40:05.000000Z"
  }
]
```

### `GET /deployments/{id}/history`
- **Summary**: Get Deployment Audit History
- **Description**: Returns chronological audit trail of state transitions (`CREATED`, `STARTED`, `TRAFFIC_SHIFT`, `FAILURE_INJECTED`, `AUTO_ROLLBACK`, `MANUAL_ROLLBACK`).
- **Status Code**: `200 OK`
- **Response Example**:
```json
[
  {
    "id": 3,
    "deployment_id": 1,
    "event_type": "TRAFFIC_SHIFT",
    "message": "Traffic shifted: Stable 75.0% / Canary 25.0%.",
    "details": "{\"stable\": 75.0, \"canary\": 25.0}",
    "timestamp": "2026-10-05T09:35:00.000000Z"
  },
  {
    "id": 2,
    "deployment_id": 1,
    "event_type": "STARTED",
    "message": "Canary rollout lifecycle activated. State transitioned to RUNNING.",
    "details": "{\"status\": \"RUNNING\"}",
    "timestamp": "2026-10-05T09:30:15.000000Z"
  },
  {
    "id": 1,
    "deployment_id": 1,
    "event_type": "CREATED",
    "message": "Deployment created with Stable (v1.0.0) and Canary (v2.0.0).",
    "details": "{\"threshold\": 10.0, \"stable\": \"v1.0.0\", \"canary\": \"v2.0.0\"}",
    "timestamp": "2026-10-05T09:30:00.000000Z"
  }
]
```

---

## 7. Planned Endpoints for Subsequent Phases

### Automated Circuit Breaker & Controlled Failure Injection (Phases 9 & 10)
- `POST /deployments/{id}/failure` - Inject synthetic failure rate into canary version (v2)
- `POST /deployments/{id}/rollback` - Manually trigger rollback to 100% stable
