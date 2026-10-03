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

### `DELETE /deployments/{id}`
- **Summary**: Delete Deployment
- **Description**: Permanently deletes a deployment with cascading deletion of all associated versions, traffic configs, metrics, and logs.
- **Status Code**: `204 No Content`

### `POST /deployments/{id}/start`
- **Summary**: Start Canary Rollout
- **Description**: Activates deployment by transitioning status from `PENDING` to `RUNNING`.
- **Status Code**: `200 OK`

---

## 4. Stable v1 & Canary v2 Simulation Endpoints (Implemented - Phase 6)

### `POST /deployments/{id}/simulate/version/{version_type}`
- **Summary**: Simulate Requests Directly to Target Version
- **Description**: Executes N simulated requests directly against either the `STABLE` or `CANARY` instance. Measures latency with realistic jitter (+/- 10%) and emulates synthetic HTTP 500 error packets according to the configured `failure_rate`.
- **Path Parameters**:
  - `id`: Deployment ID
  - `version_type`: `STABLE` or `CANARY`
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "count": 5,
  "payload": {
    "action": "process_checkout",
    "amount": 49.99
  }
}
```
- **Response Example**:
```json
{
  "deployment_id": 1,
  "deployment_name": "Payment Gateway Microservice",
  "version_type": "CANARY",
  "version_tag": "v2.0.0",
  "total_requests": 5,
  "successful_requests": 4,
  "failed_requests": 1,
  "error_rate": 20.0,
  "avg_latency_ms": 48.34,
  "results": [
    {
      "request_id": "req-9c8e104e76a1",
      "version_type": "CANARY",
      "version_tag": "v2.0.0",
      "status": "SUCCESS",
      "status_code": 200,
      "latency_ms": 47.12,
      "error_message": null,
      "headers": {
        "X-Request-Id": "req-9c8e104e76a1",
        "X-Amzn-Trace-Id": "Root=1-670001a2-abc1234567890def",
        "X-App-Version": "v2.0.0",
        "X-Target-Group": "tg-canary",
        "X-Simulated-Latency": "47.12ms"
      },
      "timestamp": "2026-10-03T17:35:00.000000Z"
    }
  ]
}
```

### `GET /deployments/{id}/versions`
- **Summary**: Get Deployment Versions
- **Description**: Lists both version instances (`STABLE` and `CANARY`) with their latency, failure rate, and image tags.
- **Status Code**: `200 OK`

### `PUT /deployments/{id}/versions/{version_type}`
- **Summary**: Configure Version Simulation Parameters
- **Description**: Dynamically updates version runtime parameters such as simulated latency (ms), synthetic failure rate (`0.0` to `1.0`), and active status.
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "simulated_latency_ms": 65.0,
  "failure_rate": 0.25,
  "is_active": true
}
```

---

## 5. Planned Endpoints for Subsequent Phases

### Weighted Traffic Splitting & Dynamic Routing (Phase 7)
- `POST /deployments/{id}/traffic` - Adjust stable vs canary traffic distribution (e.g., 90/10, 75/25, 50/50, 0/100)
- `POST /deployments/{id}/simulate` - Dispatch simulated requests across traffic split

### Observability, Logs & Metrics (Phase 8)
- `GET /deployments/{id}/metrics` - Query real-time metrics (success, error rate, latency)
- `GET /deployments/{id}/logs` - Inspect structured application logs
- `GET /deployments/{id}/history` - View chronological state transitions and rollback events

### Automated Circuit Breaker & Failure Injection (Phases 9 & 10)
- `POST /deployments/{id}/failure` - Inject synthetic failure rate into canary version (v2)
- `POST /deployments/{id}/rollback` - Manually trigger rollback to 100% stable
