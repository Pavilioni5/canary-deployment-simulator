# API Documentation - Canary Deployment Simulator (P71)

## Overview
This document specifies the REST API endpoints provided by the Canary Deployment Simulator backend built using FastAPI.

## Interactive API Docs
When running locally:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Planned Core Endpoints

### 1. Authentication & Authorization
- `POST /auth/register` - Register a new user account (Admin/User role)
- `POST /auth/login` - Authenticate credentials and receive JWT access token
- `GET /auth/me` - Retrieve current user profile and permissions

### 2. Deployment Management
- `POST /deployments` - Create a new deployment with stable (v1) and canary (v2) configs
- `GET /deployments` - List all deployments
- `GET /deployments/{id}` - Retrieve details of a specific deployment
- `POST /deployments/{id}/start` - Launch canary traffic shifting

### 3. Canary Traffic Control & Simulation
- `POST /deployments/{id}/traffic` - Adjust stable vs canary traffic distribution (e.g., 90/10, 75/25, 50/50, 0/100)
- `POST /deployments/{id}/simulate` - Dispatch simulated requests across traffic split
- `POST /deployments/{id}/failure` - Inject synthetic failure rate into canary version (v2)
- `POST /deployments/{id}/rollback` - Manually trigger rollback to 100% stable

### 4. Observability, Logs & Metrics
- `GET /deployments/{id}/metrics` - Query real-time metrics (success, error rate, latency)
- `GET /deployments/{id}/logs` - Inspect structured application logs
- `GET /deployments/{id}/history` - View chronological state transitions and rollback events
