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

---

## Frontend Dashboard Architecture (Phase 11)

The frontend client is implemented with React 18 and Vite, utilizing a Vanilla CSS Design System with zero Tailwind dependencies:

```text
[App.jsx] (Root State & Polling Manager)
  |-- [Navbar.jsx] (Brand Badge, Health Ping, Deployment Switcher, JWT Auth)
  |-- [RollbackBanner.jsx] (Emergency Circuit Breaker Notice & Operator Rollback Trigger)
  |-- [Tabbed View Container]
        |-- Tab 1: [TopologyCard.jsx] (AWS ALB Ingress, Weighted Target Groups, Fleet Cards)
        |-- Tab 2: [TrafficControlCard.jsx] (Slider, Presets, Batch Traffic Dispatcher)
        |-- Tab 3: [ChaosControlCard.jsx] (Failure Rate Slider, Fault Profile Pickers)
        |-- Tab 4: [TelemetryPanel.jsx] (KPI Stats, Threshold Monitor, Live Packet Trace Table)
        |-- Tab 5: [AuditLogsPanel.jsx] (Lifecycle Audit History, System Diagnostic Logs)
  `-- [CreateDeploymentModal.jsx] (Provisioning Dialog for Canary Rollouts)
```

### Key Frontend Capabilities
- **Pure Vanilla CSS System**: Custom design tokens for dark mode, glassmorphism, glowing status chips, and typography (`Inter` & `JetBrains Mono`).
- **Real-Time Polling Engine**: 3.5-second polling synchronization fetching live metrics, circuit breaker status, and logs.
- **Circuit Breaker Reactivity**: Instantly alerts the operator with animated red banners when error thresholds are breached and traffic is rolled back.

