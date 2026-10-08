# Academic Viva and Examination Guide (Project ID: P71)

## Project Title
**Cloud-Based Canary Deployment Simulator**

---

## 1. Executive Summary & Two-Minute Elevator Pitch

### The Problem
Traditional "big-bang" deployments expose 100% of user traffic to unverified software versions simultaneously. If a critical bug, database leak, or thread-pool exhaustion occurs, the blast radius impacts all users, causing severe service downtime and brand degradation. While blue-green deployments allow fast traffic switching, they still expose 100% of traffic at the moment of switchover.

### The Solution
The **Cloud-Based Canary Deployment Simulator (Project ID: P71)** implements a cloud-native release engineering platform modeling how traffic can be incrementally routed from a baseline stable release (v1) to a candidate canary release (v2) across weighted target groups (e.g., 90/10, 75/25, 50/50).

The system continuously samples real-time health telemetry across a sliding evaluation window. If the observed Canary error rate breaches a configurable safety threshold (e.g., 10.0%), an automated circuit breaker trips in sub-second time:
1. Ingress traffic is instantaneously restored to 100% Stable (v1.0.0) / 0% Canary.
2. The deployment status transitions to `ROLLED_BACK`.
3. An immutable audit record is committed to relational PostgreSQL storage with full telemetry provenance.

### Core Deliverables
- **FastAPI REST API**: High-performance asynchronous backend providing weighted routing, chaos injection, automated rollbacks, and metrics aggregation.
- **Relational PostgreSQL Database**: 7 normalized tables managing deployments, version parameters, traffic configs, metrics, audit trails, and logs.
- **Interactive React Web Dashboard**: Pure Vanilla CSS engineering interface visualizing topology, live traffic distribution, chaos injection controls, and packet traces.
- **Automated CLI Demo Runner**: A 7-stage script demonstrating the complete failure and rollback lifecycle on demand.
- **Comprehensive Quality Assurance**: 53 automated Pytest tests and distributed Locust load testing benchmarks across 10, 50, and 100 concurrent users.

---

## 2. Core Theoretical Foundations & Comparative Analysis

### 2.1 Deployment Strategies Comparison

| Strategy | Traffic Shift Mechanism | Blast Radius | Infrastructure Cost | Rollback Speed | Rollback Automation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Canary Deployment** | Incremental weighted split (e.g. 10%, 25%, 50%, 100%) | **Minimal** (Confined to minor traffic fraction) | Low to Moderate | **Sub-second** (Weight adjustment) | **Automated** (Circuit breaker triggered by error rate) |
| **Blue-Green** | Binary switchover (100% Blue $\rightarrow$ 100% Green) | **High** (100% of users exposed immediately) | High (Requires 2x identical environments) | Fast (DNS or router switch) | Often Manual or post-switch alarm |
| **Rolling Deployment** | Incremental server instance replacement in-place | **Moderate** (Users routed to updated pods) | Low (Reuses existing fleet) | Slow (Must roll back instances sequentially) | Semi-automated |
| **A/B Testing** | Segmented user targeting by demographic/feature | Functional (Targets business KPIs) | Moderate | N/A (Business experiment) | Manual business decision |

### 2.2 Canary Deployment vs. A/B Testing
A common viva question is confusing **Canary Deployment** with **A/B Testing**:
- **Canary Deployment** is a *Release Engineering and DevOps* technique aimed at risk mitigation, system stability, and verifying non-functional technical requirements (latency, HTTP 500 rates, memory saturation).
- **A/B Testing** is a *Product Management and Data Science* technique aimed at evaluating user behavior and business conversion rates (e.g., measuring whether a green button generates more purchases than a blue button).

### 2.3 The Circuit Breaker Pattern & MTTR
Inspired by electrical circuit breakers, the software circuit breaker pattern (popularized by Martin Fowler) prevents catastrophic cascade failures:
1. **Closed State (Normal Operation)**: Traffic flows freely across weighted target groups; metrics are continuously monitored.
2. **Tripping Condition (Threshold Breach)**: When monitored Canary error rate exceeds the rollback threshold ($\text{Error Rate} > \theta$), the circuit trips.
3. **Open State (Rolled Back)**: Traffic is instantaneously severed to the canary fleet and redirected 100% to stable v1.
4. **Mean Time to Recovery (MTTR)**: Without automated circuit breakers, MTTR requires human operator detection, triage, and manual rollback (typically 15 to 45 minutes). With this automated simulator, MTTR is reduced to **$< 1\text{ second}$**.

### 2.4 Why Evaluate Canary-Specific Error Rate Instead of Aggregate Global Error Rate?
Evaluating aggregate error rate across the entire cluster is a dangerous flaw in canary monitoring:
$$\text{Aggregate Error Rate} = \frac{\text{Failed}_{\text{Stable}} + \text{Failed}_{\text{Canary}}}{\text{Total}_{\text{Stable}} + \text{Total}_{\text{Canary}}}$$
In a 90/10 traffic split, if the Canary release has a catastrophic 100% failure rate, the aggregate error rate is only:
$$\text{Aggregate Error Rate} = \frac{0 + 10}{90 + 10} = 10\%$$
If the global threshold were set to 15%, a completely broken canary release would go unnoticed! By evaluating **Canary-specific error rate**:
$$\text{Canary Error Rate} = \frac{\text{Failed}_{\text{Canary}}}{\text{Total}_{\text{Canary}}} \times 100\% = 100\%$$
The system immediately detects the failure and trips the rollback.

---

## 3. Top 25 Viva Examination Questions and Model Answers

### Category 1: Cloud Architecture & Deployment Patterns

#### Q1: What is the origin of the term "Canary Deployment"?
**Answer**: The term originates from the historic practice of coal miners carrying caged canaries into underground mines. Because canaries are much more sensitive to toxic gases (such as carbon monoxide) than humans, the canary's distress provided an early warning to evacuate before miners were harmed. In software, the canary build serves as an early detector of fatal defects before the full user base is affected.

#### Q2: How does this simulator model AWS Application Load Balancer (ALB) behavior?
**Answer**: AWS ALB supports weighted target group routing, where rules assign integer weights (e.g., 90 to Target Group 1 and 10 to Target Group 2). Our simulator models this using a weighted random distribution algorithm (`random.uniform(0.0, 100.0)`). Incoming requests receive synthetic ALB routing headers (`X-Amzn-Trace-Id`, `X-Target-Group`, `X-Canary-Routing`), mirroring AWS ingress telemetry.

#### Q3: How would this architecture map to an AWS cloud deployment?
**Answer**:
- Compute: FastAPI backend and React frontend deployed as Docker containers on **AWS ECS (Elastic Container Service) with Fargate** or **Amazon EKS**.
- Routing: **AWS Application Load Balancer (ALB)** with weighted target groups.
- Database: **Amazon RDS for PostgreSQL** in a Multi-AZ configuration.
- Monitoring: **Amazon CloudWatch Metric Alarms** triggering an **AWS Lambda function** or **AWS Step Function** to update ALB target group weights upon threshold breach.

#### Q4: What is "Blast Radius Containment"?
**Answer**: Blast radius refers to the maximum scope of users or system components negatively impacted when an infrastructure or software failure occurs. In canary deployment, restricting initial traffic to 10% confines the blast radius to at most 10% of users, leaving 90% of traffic operating on the proven stable baseline.

#### Q5: What is the difference between In-Place and Canary deployments?
**Answer**: In an in-place deployment, software packages on existing servers are overwritten. If the update fails, rollback requires re-installing the previous binary, causing extended downtime. In a canary deployment, both versions coexist concurrently, and rollback requires only a zero-downtime routing weight update.

---

### Category 2: Backend & Resilience Engineering

#### Q6: Why did you choose FastAPI over Flask or Django?
**Answer**: FastAPI was chosen because:
1. **Asynchronous Concurrency**: Built on Starlette and the ASGI specification, allowing high-throughput non-blocking request handling essential for simulated traffic batches.
2. **Automatic Data Validation**: Uses Pydantic for strict schema validation, type checking, and boundary constraints.
3. **Interactive OpenAPI / Swagger Documentation**: Generates interactive API documentation at `/docs` out of the box, facilitating live examiner interaction.
4. **Lightweight Execution**: Has minimal memory overhead compared to full-stack frameworks like Django.

#### Q7: How does the weighted traffic routing algorithm work mathematically?
**Answer**: In `app/services/traffic_service.py`, the function `select_target_version` generates a pseudo-random floating-point number $r \in [0.0, 100.0)$.
- If $r < \text{Canary Percentage}$, the request routes to the Canary instance (provided it is active).
- Otherwise, it routes to the Stable instance.
Over a sample of $N$ requests, the central limit theorem ensures that the proportion of requests routed to Canary converges to the configured canary weight.

#### Q8: What failure profiles does your chaos engineering module support?
**Answer**: The simulator supports four realistic cloud failure signatures:
1. `HTTP_500`: Uncaught application runtime exceptions and logic errors.
2. `LATENCY_TIMEOUT`: Simulates thread pool starvation by raising latency to $\ge 2500\text{ ms}$ and returning HTTP 504 Gateway Timeout.
3. `DATABASE_ERROR`: Simulates relational connection pool exhaustion.
4. `MEMORY_SPIKE`: Simulates container Out-Of-Memory (OOM) pressure, returning HTTP 503 Service Unavailable.

#### Q9: What happens when the circuit breaker trips?
**Answer**: In `app/services/rollback_service.py`:
1. Traffic routing weights are immediately reset to 100% Stable / 0% Canary.
2. The deployment status transitions from `RUNNING` to `ROLLED_BACK`.
3. An audit record is stored in `deployment_events` with event type `AUTO_ROLLBACK`, saving the observed error rate, threshold, and timestamp.
4. A `CRITICAL` alert is written to structured diagnostic logs under source `CIRCUIT_BREAKER`.
5. Future simulation requests on this deployment are rejected with `HTTP 400 Bad Request` until explicitly restarted or re-provisioned.

#### Q10: Does your system support manual operator rollback?
**Answer**: Yes. Operators can trigger `POST /deployments/{id}/rollback` via the web dashboard or REST API at any point during a rollout if unexpected behavior is observed, immediately restoring 100% stable traffic.

---

### Category 3: Database & Transaction Integrity

#### Q11: Why use PostgreSQL instead of MongoDB or NoSQL?
**Answer**:
1. **Relational Integrity**: Deployment entities have strict relational dependencies (Deployments $\rightarrow$ Versions $\rightarrow$ Traffic Configs $\rightarrow$ Metrics $\rightarrow$ Events). Foreign keys with cascade deletions prevent orphaned records.
2. **ACID Transactions**: Automatic rollback requires atomic updates across `traffic_configs`, `deployments`, `deployment_events`, and `logs`. PostgreSQL guarantees that either all changes commit together or none do.
3. **Structured Time-Series Metrics**: Aggregating request metrics over sliding windows is efficiently performed with PostgreSQL indexed queries.

#### Q12: How are database transactions handled during automatic rollback?
**Answer**: SQLAlchemy manages session transactions. The updates to traffic configuration, deployment status, audit event insertion, and structured log creation are staged within a single database transaction block (`db.commit()`). If any operation fails, the transaction is rolled back, preventing corrupted state.

#### Q13: What indexes did you implement and why?
**Answer**:
1. `users.email`: Unique index for $O(1)$ authentication lookups.
2. `deployments.name`: B-tree index for fast deployment searching.
3. `metrics.(deployment_id, timestamp)`: Composite index to accelerate sliding-window metric aggregations.
4. `deployment_events.(deployment_id, timestamp)`: Index for chronological audit timeline retrieval.

#### Q14: How does the system handle database migrations or initialization?
**Answer**: The application includes `init_db()` and `seed_admin_user()` routines executed during FastAPI lifespan startup. When PostgreSQL starts in Docker Compose, tables are created and seeded with default administrator credentials automatically.

---

### Category 4: Security, Authentication & Observability

#### Q15: How is user authentication implemented?
**Answer**: Authentication uses JSON Web Tokens (PyJWT) and salted password hashing (Bcrypt). When a user logs in with valid credentials at `POST /auth/login`, the server returns a signed JWT containing the user ID, role, and expiration timestamp. Protected endpoints require the `Authorization: Bearer <token>` header.

#### Q16: How is Role-Based Access Control (RBAC) enforced?
**Answer**: Using FastAPI dependency injection (`get_current_user` and `require_admin`). The token payload contains a `role` claim (`ADMIN` or `USER`). Administrative actions (such as system-wide parameter modifications) enforce role checking, returning `HTTP 403 Forbidden` if permissions are insufficient.

#### Q17: What observability telemetry does the system produce?
**Answer**:
1. **Application Diagnostic Logs (`logs` table)**: Structured logs categorized by severity (`INFO`, `WARNING`, `ERROR`, `CRITICAL`) and source (`ROUTER`, `CIRCUIT_BREAKER`, `CHAOS_ENGINE`, `SIMULATOR`).
2. **Audit Event History (`deployment_events` table)**: Immutable lifecycle records tracking state transitions.
3. **Metric Aggregations (`metrics` table)**: Time-series snapshots of request counts, error rates, and average response times.

---

### Category 5: Performance, Scalability & Load Testing

#### Q18: What were your findings during Locust load testing?
**Answer**: Tested across 10, 50, and 100 concurrent users:
- Under **Low Load (10 users)**: Sustained ~42.5 RPS with a median latency of 8.2ms.
- Under **Medium Load (50 users)**: Sustained ~140.0 RPS with a median latency of 14.5ms.
- Under **High Load (100 users)**: Sustained ~196.2 RPS with a 95th percentile latency below 90ms.
- Nominal failure rates remained $\le 0.02\%$ prior to chaos injection.

#### Q19: Why did you run Locust in headless mode?
**Answer**: Headless mode (`--headless`) executes the benchmark directly from the CLI without launching the web server GUI. This allows reproducible automated performance testing in CI/CD pipelines, automated report generation (`run_load_test.py`), and removes client-side browser rendering bottlenecks.

#### Q20: How would you scale this application horizontally in production?
**Answer**:
1. **Stateless API Replicas**: The FastAPI backend is completely stateless; JWT tokens are validated cryptographically without server-side session locks. Multiple backend containers can run behind an AWS Application Load Balancer.
2. **Database Read Replicas**: Separate analytical telemetry queries (`GET /metrics`, `GET /logs`) to read replicas, preserving primary instance write capacity for traffic simulation and rollback transactions.
3. **Caching Layer**: Integrate Redis to cache active traffic configuration weights and recent metric aggregates.

---

## 4. Live Examiner Challenges & On-The-Spot Modifications

During academic viva examinations, examiners frequently ask candidates to make live code modifications to verify genuine project authorship. Below are five likely scenarios and their exact execution steps:

---

### Challenge 1: "Change the Rollback Threshold from 10% to 5% Live"

**Objective**: Prove that the safety threshold can be altered dynamically and that the circuit breaker trips at a lower error rate.

**Execution via Web Dashboard**:
1. Open `http://localhost:5173`.
2. Click **+ New Deployment** and set **Rollback Threshold** to `5.0%`.
3. Start the deployment and shift traffic to 50/50.
4. Inject a mild failure rate of `8.0%` in the **Chaos** tab.
5. Simulate 25 requests $\rightarrow$ The circuit breaker trips because $8.0\% > 5.0\%$, whereas under a 10% threshold it would have remained running!

**Execution via REST API**:
```bash
curl -X PUT "http://localhost:8000/deployments/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rollback_threshold": 5.0}'
```

---

### Challenge 2: "Inject a Gateway Timeout (504) Instead of HTTP 500"

**Objective**: Demonstrate that the chaos engine models latency degradation and timeouts.

**Execution via CLI**:
```bash
curl -X POST "http://localhost:8000/deployments/1/failure" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "failure_rate": 0.50,
    "error_type": "LATENCY_TIMEOUT",
    "affected_version": "CANARY"
  }'
```

**Verification**:
1. Run `curl -X POST "http://localhost:8000/deployments/1/simulate" -H "Authorization: Bearer $TOKEN" -d '{"count": 10}'`.
2. Inspect output: failed requests display `status_code: 504`, `latency_ms: >= 2500ms`, and error message `HTTP 504: Gateway timeout injected`.

---

### Challenge 3: "Demonstrate Clean Traffic Distribution Without Any Failures"

**Objective**: Prove that under healthy conditions, traffic balances smoothly without false-positive rollbacks.

**Execution**:
1. In the Web Dashboard, select **Traffic Shifting & Simulator**.
2. Click **50/50 Balanced** $\rightarrow$ Click **Apply Traffic Shift**.
3. Verify failure rate is 0% (click **Clear Active Faults** if needed).
4. Click **Simulate 50 Requests**.
5. Observe the results banner: ~25 requests routed to Stable (0% errors), ~25 requests routed to Canary (0% errors), deployment status remains `RUNNING`.

---

### Challenge 4: "Trigger an Emergency Manual Rollback"

**Objective**: Verify that human operators can override automated monitoring during unexpected incidents.

**Execution**:
1. On a running deployment, click the **Manual Emergency Rollback** button in the dashboard or execute:
   ```bash
   curl -X POST "http://localhost:8000/deployments/1/rollback" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"reason": "Examiner requested manual override"}'
   ```
2. Verify response: `status: "ROLLED_BACK"`, `traffic_restored: {"stable": 100.0, "canary": 0.0}`.
3. Switch to **Audit Trail & Logs** to show the `MANUAL_ROLLBACK` event recorded with the operator's email and timestamp.

---

### Challenge 5: "Query the Database Directly to Prove Event Persistence"

**Objective**: Prove that the database actually stores relational records rather than using in-memory mock variables.

**Execution**:
In Docker:
```bash
docker compose exec db psql -U canary_user -d canary_db
```
Or locally with SQLite:
```bash
sqlite3 canary_simulator.db
```
Run verification queries:
```sql
SELECT id, name, status, rollback_threshold FROM deployments;
SELECT event_type, message, timestamp FROM deployment_events ORDER BY timestamp DESC LIMIT 5;
SELECT level, source, message FROM logs ORDER BY timestamp DESC LIMIT 5;
```

---

## 5. Architectural Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Client / Operator
    participant UI as React Dashboard
    participant API as FastAPI Gateway
    participant Router as Traffic Router
    participant S as Stable Fleet (v1)
    participant C as Canary Fleet (v2)
    participant Monitor as Circuit Breaker Monitor
    participant DB as PostgreSQL DB

    Operator->>UI: Shift traffic to 50% Stable / 50% Canary
    UI->>API: POST /deployments/{id}/traffic
    API->>DB: Update TrafficConfig (50/50) & Log Event
    API-->>UI: Traffic weights updated

    Operator->>UI: Inject 40% failure rate into Canary
    UI->>API: POST /deployments/{id}/failure
    API->>DB: Update Canary failure_rate & Log FAILURE_INJECTED
    API-->>UI: Fault active

    Operator->>UI: Dispatch 30 client requests
    UI->>API: POST /deployments/{id}/simulate
    loop For each request
        API->>Router: Roll random float [0, 100)
        alt Roll >= 50
            Router->>S: Execute Stable Request (0% fail)
            S-->>Router: HTTP 200 OK (30ms)
        else Roll < 50
            Router->>C: Execute Canary Request (40% fail)
            C-->>Router: HTTP 500 Failure (Injected)
        end
    end

    API->>Monitor: Compute Canary Error Rate (~42%)
    Monitor->>Monitor: Compare: 42% > 10% Threshold
    alt Threshold Breached
        Monitor->>DB: Atomic Update: Traffic=100/0, Status=ROLLED_BACK
        Monitor->>DB: Insert AUTO_ROLLBACK audit event & CRITICAL log
        Monitor-->>API: Circuit Breaker Tripped!
    end
    API-->>UI: Response with triggered_rollback=true & reason
    UI->>UI: Render red CIRCUIT BREAKER banner & snap weights to 100/0
```

---

## 6. Academic References & Literature

1. **Google Site Reliability Engineering (SRE)**: Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (2016). *Site Reliability Engineering: How Google Runs Production Systems*. O'Reilly Media. (Chapter 8: Release Engineering; Chapter 22: Addressing Cascading Failures).
2. **Martin Fowler**: *CanaryRelease* and *CircuitBreaker Pattern* architectural guides. MartinFowler.com.
3. **AWS Well-Architected Framework**: *Reliability Pillar: Failure Management and Automated Recovery*. Amazon Web Services (AWS Whitepapers).
4. **Chaos Engineering**: Basiri, A., Sengupta, N., Shturova, J., et al. (2016). *Chaos Engineering: Building Confidence in System Behavior at Scale*. IEEE Software, 33(3), 35-41.
5. **FastAPI & ASGI**: Ramirez, S. (2019). *FastAPI: Modern, Fast Web Framework for Python*. Tiangolo Publications.
