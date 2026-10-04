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
- **Description**: Dynamically configures traffic routing weights between Stable v1 and Canary v2 (e.g. 90/10, 75/25, 50/50, 0/100). Emulates AWS Application Load Balancer weighted target groups, updates the database, and records an audit log.
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "canary_percentage": 25.0,
  "stable_percentage": 75.0
}
```
*(Note: `stable_percentage` is optional; if omitted, the system computes `100.0 - canary_percentage`).*
- **Response Example**:
```json
{
  "deployment_id": 1,
  "stable_percentage": 75.0,
  "canary_percentage": 25.0,
  "last_shifted_at": "2026-10-04T17:35:00.000000Z",
  "message": "Traffic weights successfully updated to 75.0% Stable / 25.0% Canary."
}
```

### `GET /deployments/{id}/traffic`
- **Summary**: Get Current Traffic Split Configuration
- **Status Code**: `200 OK`
- **Response Example**:
```json
{
  "id": 1,
  "deployment_id": 1,
  "stable_percentage": 75.0,
  "canary_percentage": 25.0,
  "last_shifted_at": "2026-10-04T17:35:00.000000Z",
  "updated_at": "2026-10-04T17:35:00.000000Z"
}
```

### `POST /deployments/{id}/simulate`
- **Summary**: Simulate Client Traffic Across Weighted Router
- **Description**: Dispatches N client requests through the weighted traffic router. Requests are routed probabilistically to Stable v1 or Canary v2 according to active weights. Returns a detailed telemetry breakdown for both versions and the overall deployment.
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "count": 50,
  "payload": {
    "route": "/checkout",
    "user_id": 1042
  }
}
```
- **Response Example**:
```json
{
  "deployment_id": 1,
  "deployment_name": "Order Checkout Service",
  "status": "RUNNING",
  "traffic_weights": {
    "stable": 75.0,
    "canary": 25.0
  },
  "total_requests": 50,
  "stable_summary": {
    "total_requests": 38,
    "successful_requests": 38,
    "failed_requests": 0,
    "error_rate": 0.0,
    "avg_latency_ms": 42.15
  },
  "canary_summary": {
    "total_requests": 12,
    "successful_requests": 12,
    "failed_requests": 0,
    "error_rate": 0.0,
    "avg_latency_ms": 46.80
  },
  "overall_summary": {
    "total_requests": 50,
    "successful_requests": 50,
    "failed_requests": 0,
    "error_rate": 0.0,
    "avg_latency_ms": 43.27
  },
  "results": [
    {
      "request_id": "req-3fa85f64e9a1",
      "version_type": "CANARY",
      "version_tag": "v2.0.0",
      "status": "SUCCESS",
      "status_code": 200,
      "latency_ms": 45.3,
      "error_message": null,
      "headers": {
        "X-Canary-Routing": "canary",
        "X-Configured-Canary-Weight": "25.0%",
        "X-Configured-Stable-Weight": "75.0%",
        "X-App-Version": "v2.0.0"
      },
      "timestamp": "2026-10-04T17:35:10.000000Z"
    }
  ]
}
```

---

## 6. Planned Endpoints for Subsequent Phases

### Observability, Logs & Metrics (Phase 8)
- `GET /deployments/{id}/metrics` - Query real-time metrics (success, error rate, latency)
- `GET /deployments/{id}/logs` - Inspect structured application logs
- `GET /deployments/{id}/history` - View chronological state transitions and rollback events

### Automated Circuit Breaker & Controlled Failure Injection (Phases 9 & 10)
- `POST /deployments/{id}/failure` - Inject synthetic failure rate into canary version (v2)
- `POST /deployments/{id}/rollback` - Manually trigger rollback to 100% stable
