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
- **Description**: Dispatches N client requests through the weighted traffic router, evaluates health thresholds, and triggers automatic rollback if breached.
- **Status Code**: `200 OK`

---

## 6. Metrics & Observability Endpoints (Implemented - Phase 8)

### `GET /deployments/{id}/metrics`
- **Summary**: Get Aggregated Deployment Metrics
- **Description**: Returns cumulative metrics (total requests, stable/canary counts, error rates, average latency, rollback counts, and time-series snapshots).
- **Status Code**: `200 OK`

### `GET /deployments/{id}/logs`
- **Summary**: Get Deployment Application Logs
- **Description**: Inspects structured diagnostic logs with level/source filtering and pagination.
- **Status Code**: `200 OK`

### `GET /deployments/{id}/history`
- **Summary**: Get Deployment Audit History
- **Description**: Returns chronological audit trail of state transitions (`CREATED`, `STARTED`, `TRAFFIC_SHIFT`, `AUTO_ROLLBACK`, `MANUAL_ROLLBACK`).
- **Status Code**: `200 OK`

---

## 7. Rollback & Circuit Breaker Endpoints (Implemented - Phase 9)

### `POST /deployments/{id}/rollback`
- **Summary**: Manual Deployment Rollback
- **Description**: Instantly trips the circuit breaker: resets traffic routing configuration to `100% Stable / 0% Canary`, changes deployment status to `ROLLED_BACK`, appends a `MANUAL_ROLLBACK` audit record to `deployment_events`, and logs a warning.
- **Security**: Requires Bearer JWT
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "reason": "Observed elevated latency during peak load."
}
```
- **Response Example**:
```json
{
  "deployment_id": 1,
  "deployment_name": "Checkout Microservice",
  "status": "ROLLED_BACK",
  "rollback_type": "MANUAL",
  "reason": "Observed elevated latency during peak load.",
  "rollback_threshold": 10.0,
  "observed_canary_error_rate": null,
  "traffic_restored": {
    "stable": 100.0,
    "canary": 0.0
  },
  "timestamp": "2026-10-05T10:15:00.000000Z"
}
```

### Automated Circuit-Breaker Rollback Mechanics (Executed via `/simulate`)
During client traffic simulation (`POST /deployments/{id}/simulate`):
1. The health monitor calculates the Canary error rate:
   $$\text{Canary Error Rate} = \left( \frac{\text{Failed Canary Requests}}{\text{Total Canary Requests}} \right) \times 100\%$$
2. If `Canary Error Rate > Rollback Threshold`:
   - System immediately resets traffic: `Stable = 100.0%`, `Canary = 0.0%`.
   - Deployment status transitions to `ROLLED_BACK`.
   - An `AUTO_ROLLBACK` event is stored in `deployment_events` detailing the threshold, actual error rate, and incident timestamp.
   - A `CRITICAL` log is written to `logs` and stdout.
   - Subsequent simulation calls on this deployment are rejected with `HTTP 400 Bad Request`.

---

## 8. Planned Endpoints for Subsequent Phases

### Controlled Failure Injection (Phase 10)
- `POST /deployments/{id}/failure` - Dedicated endpoint to configure artificial failure scenarios for live viva demonstration
