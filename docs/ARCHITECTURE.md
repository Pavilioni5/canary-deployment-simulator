# Architecture Documentation - Canary Deployment Simulator (P71)

## Overview
The Cloud-Based Canary Deployment Simulator models an automated, safe deployment pipeline. It routes incoming client requests between two versions:
- **Stable Version (v1)**: Baseline production release.
- **Canary Version (v2)**: Candidate release receiving a controlled percentage of traffic.

## Architectural Flow

```text
User / Browser / Client
          |
   React Dashboard
          |
  FastAPI REST API (Backend)
          |
  Authentication Layer (JWT)
          |
Canary Deployment Controller
          |
    Traffic Router
    /            \
Stable (v1)     Canary (v2)
    \            /
   Health Monitor & Error Watcher
          |
      PostgreSQL
          |
 CloudWatch / Structured Logs
```

## Mermaid Diagram

```mermaid
graph TD
    Client["Client / User"] --> Frontend["React Dashboard (Vite)"]
    Frontend --> API["FastAPI REST API"]
    API --> Auth["JWT Security Middleware"]
    Auth --> Controller["Canary Deployment Controller"]
    Controller --> Router["Traffic Router"]
    
    Router -->|P% Traffic| Canary["Canary Version (v2)"]
    Router -->|(100-P)% Traffic| Stable["Stable Version (v1)"]
    
    Canary --> Metrics["Metrics Collector & Health Watcher"]
    Stable --> Metrics
    
    Metrics -->|Persist Logs & History| DB[("PostgreSQL Database")]
    Metrics -->|Error Rate > Threshold| Rollback["Automatic Rollback Engine"]
    Rollback -->|Force 100% Stable| Router
```

## Core Cloud & Architectural Components
1. **Compute / Container Execution**: FastAPI and React running as Docker containers (AWS EC2 / ECS compatible).
2. **Database**: PostgreSQL (AWS RDS compatible) for structured deployment logs, audit events, and metrics.
3. **Traffic Router & Controller**: Weighted routing simulating Application Load Balancer (ALB) target group weight adjustments.
4. **Monitoring & Alerting**: Metrics collection mimicking AWS CloudWatch Alarms for automated rollback triggering.
