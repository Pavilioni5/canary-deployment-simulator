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
- **Response Example**:
```json
{
  "status": "healthy",
  "timestamp": "2026-10-03T05:40:00.000000Z",
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

## 2. Authentication & Authorization Endpoints (Implemented - Phase 4)

All protected routes require an HTTP Authorization header in the Bearer format:
```text
Authorization: Bearer <access_token>
```

### `POST /auth/register`
- **Summary**: Register New User Account
- **Description**: Creates a new user with bcrypt password hashing and assigns an RBAC role (`USER` or `ADMIN`).
- **Status Code**: `201 Created`
- **Request Body**:
```json
{
  "email": "engineer@canary.local",
  "password": "SecurePassword123!",
  "full_name": "DevOps Engineer",
  "role": "USER"
}
```
- **Response Example**:
```json
{
  "id": 1,
  "email": "engineer@canary.local",
  "full_name": "DevOps Engineer",
  "role": "USER",
  "is_active": true,
  "created_at": "2026-10-03T05:41:00.000000Z"
}
```

### `POST /auth/login`
- **Summary**: User Login & JWT Generation
- **Description**: Validates email and salted bcrypt hash, returning a signed JWT access token.
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "email": "engineer@canary.local",
  "password": "SecurePassword123!"
}
```
- **Response Example**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60,
  "user_id": 1,
  "email": "engineer@canary.local",
  "role": "USER",
  "full_name": "DevOps Engineer"
}
```

### `GET /auth/me`
- **Summary**: Current Authenticated User Profile
- **Description**: Returns profile and role claims of the currently authenticated user.
- **Security**: Requires Bearer JWT
- **Status Code**: `200 OK`
- **Response Example**:
```json
{
  "id": 1,
  "email": "engineer@canary.local",
  "full_name": "DevOps Engineer",
  "role": "USER",
  "is_active": true,
  "created_at": "2026-10-03T05:41:00.000000Z"
}
```

### `GET /auth/admin-only`
- **Summary**: RBAC Protected Demo Route
- **Description**: Demonstrates Role-Based Access Control. Returns `200 OK` for users with `ADMIN` role; returns `403 Forbidden` for standard `USER` accounts.
- **Security**: Requires Bearer JWT with `role == "ADMIN"`
- **Status Code**: `200 OK` or `403 Forbidden`
- **Response Example (Admin)**:
```json
{
  "message": "Access granted to admin-only area.",
  "admin_email": "admin@canary.local",
  "role": "ADMIN"
}
```

---

## 3. Planned Endpoints for Subsequent Phases

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
