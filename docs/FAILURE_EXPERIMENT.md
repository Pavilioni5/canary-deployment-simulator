# Controlled Failure Scenario and Automatic Rollback Experiment (Project ID: P71)

## 1. Academic Experiment Objective

The primary objective of this experiment is to evaluate the fault detection and automated recovery capabilities of the Canary Deployment Simulator. By systematically injecting synthetic faults into the Canary instance (v2) under active weighted traffic distribution, the system demonstrates blast radius containment and automated circuit-breaker rollback when monitored error rates exceed configured thresholds.

---

## 2. Theoretical Background and Chaos Engineering Principles

In cloud-native architectures, canary deployments serve as a proactive risk mitigation technique. Rather than replacing an entire fleet at once (in-place or big-bang deployment), traffic is incrementally shifted.

However, a canary deployment is only as reliable as its monitoring and rollback mechanism. The controlled failure injection module implements chaos engineering principles:
1. **Hypothesis**: Injecting a failure rate exceeding the predefined threshold on the canary candidate will trigger automated traffic diversion within one evaluation cycle, preserving overall system availability.
2. **Blast Radius Minimization**: Because only a minority fraction of traffic (e.g., 10% to 50%) is routed to the canary, most end-users remain isolated on the healthy stable version (v1).
3. **Automated Mean Time to Recovery (MTTR)**: Without human operator intervention, the system trips an automated circuit breaker, restoring 100% traffic to stable v1 in sub-second time.

---

## 3. Supported Fault Injection Profiles

The simulator supports four distinct failure profiles representing standard real-world cloud infrastructure anomalies:

| Profile Identifier | Simulated Condition | Resulting HTTP Status | Observability Signature |
| :--- | :--- | :--- | :--- |
| `HTTP_500` | Unhandled application exception / logic crash | 500 Internal Server Error | Stack trace emulation, error rate increase |
| `LATENCY_TIMEOUT` | Upstream service degradation or thread exhaustion | 504 Gateway Timeout | Latency spikes to >= 2500ms, timeout errors |
| `DATABASE_ERROR` | Database connection pool exhaustion or network partition | 500 Internal Server Error | `DatabaseConnectionError` exception log |
| `MEMORY_SPIKE` | Memory leak or container OOM pressure | 503 Service Unavailable | `OutOfMemory` condition, service throttling |

---

## 4. Experiment Parameters

- **Deployment ID**: `1` (or target active deployment)
- **Stable Version (v1.0.0)**: Healthy baseline with `failure_rate = 0.0` (0%) and average latency of 30ms.
- **Canary Version (v2.0.0)**: Candidate release under evaluation.
- **Rollback Threshold**: `10.0%` (configurable from 1.0% to 100.0%).
- **Traffic Split**: 50% Stable / 50% Canary.
- **Batch Size**: 25 to 50 requests per evaluation cycle.

---

## 5. Step-by-Step Reproduction Guide

### Step 1: Authenticate and Obtain JWT Bearer Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@canary.local", "password": "AdminSecurePassword123!"}'
```

Extract the `access_token` from the JSON response and export it as an environment variable:

```bash
export TOKEN="<your_jwt_access_token>"
```

### Step 2: Create and Start a Monitored Deployment

```bash
curl -X POST "http://localhost:8000/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Checkout Service Resiliency Experiment",
    "description": "Validation of automated circuit breaker rollback under chaos injection",
    "rollback_threshold": 10.0,
    "evaluation_window_seconds": 60,
    "stable_tag": "v1.0.0",
    "canary_tag": "v2.0.0",
    "stable_latency_ms": 35.0,
    "canary_latency_ms": 40.0,
    "initial_canary_failure_rate": 0.0
  }'
```

Start the deployment lifecycle:

```bash
curl -X POST "http://localhost:8000/deployments/1/start" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Shift Traffic to 50% Stable / 50% Canary

```bash
curl -X POST "http://localhost:8000/deployments/1/traffic" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stable_percentage": 50.0,
    "canary_percentage": 50.0
  }'
```

Verify healthy traffic routing prior to fault injection:

```bash
curl -X POST "http://localhost:8000/deployments/1/simulate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"count": 20}'
```

Expected result: 0% Canary error rate; status remains `RUNNING`.

### Step 4: Inject Controlled Failure into Canary Candidate

Inject a 35% failure rate (`failure_rate: 0.35`) with fault profile `HTTP_500` into the Canary release:

```bash
curl -X POST "http://localhost:8000/deployments/1/failure" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "failure_rate": 0.35,
    "error_type": "HTTP_500",
    "affected_version": "CANARY"
  }'
```

**Expected Response**:
```json
{
  "deployment_id": 1,
  "deployment_name": "Checkout Service Resiliency Experiment",
  "affected_version": "CANARY",
  "version_tag": "v2.0.0",
  "failure_rate": 0.35,
  "failure_percentage": 35.0,
  "error_type": "HTTP_500",
  "simulated_latency_ms": 40.0,
  "status": "FAILURE_INJECTED",
  "message": "Controlled failure injected into v2.0.0 (CANARY): failure_rate=35.0%, error_type='HTTP_500'.",
  "timestamp": "2026-10-05T13:30:00Z"
}
```

### Step 5: Dispatch Client Traffic and Observe Circuit Breaker

Dispatch a batch of 30 client requests across the weighted target groups:

```bash
curl -X POST "http://localhost:8000/deployments/1/simulate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"count": 30}'
```

**System Behavior**:
1. Client requests are split ~50/50 between Stable and Canary.
2. Approximately 35% of Canary requests fail with HTTP 500 status codes.
3. Observed Canary error rate reaches ~30% - 40%, breaching the configured 10.0% threshold.
4. The automated circuit breaker trips synchronously:
   - Traffic routing weights immediately reset to **100% Stable / 0% Canary**.
   - Deployment status transitions from `RUNNING` to `ROLLED_BACK`.
   - `triggered_rollback` flag is set to `true` in response.

### Step 6: Verify Telemetry and Audit Trail

#### 1. Audit Trail Verification
Retrieve deployment lifecycle events:

```bash
curl -X GET "http://localhost:8000/deployments/1/history" \
  -H "Authorization: Bearer $TOKEN"
```

Verify that the following sequential events exist:
- `TRAFFIC_SHIFT`: Traffic shifted to 50/50.
- `FAILURE_INJECTED`: Details recording the 35% failure rate and fault profile.
- `AUTO_ROLLBACK`: Documenting the exact canary error rate that breached the 10.0% threshold.

#### 2. Observability Log Verification
Retrieve structured application logs:

```bash
curl -X GET "http://localhost:8000/deployments/1/logs" \
  -H "Authorization: Bearer $TOKEN"
```

Verify log entries:
- `source: "CHAOS_ENGINE"`, `level: "WARNING"`, describing the fault injection parameter update.
- `source: "CIRCUIT_BREAKER"`, `level: "CRITICAL"`, announcing circuit breaker activation.

---

## 6. Clearing Injected Faults

To reset synthetic failure rates back to 0.0% without redeploying:

```bash
curl -X DELETE "http://localhost:8000/deployments/1/failure" \
  -H "Authorization: Bearer $TOKEN"
```

Or via POST payload:

```bash
curl -X POST "http://localhost:8000/deployments/1/failure" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"failure_rate": 0.0, "affected_version": "CANARY"}'
```

---

## 7. Viva Discussion Points

1. **Why does the circuit breaker evaluate canary error rate instead of overall error rate?**
   - In a 90/10 traffic split, a 100% failure rate in the canary would only represent 10% of the aggregate traffic, potentially masking critical failures if evaluated globally. Isolating canary telemetry prevents bad code from surviving small initial splits.
2. **What happens to in-flight requests during rollback?**
   - The weighted routing table updates instantaneously. Subsequent requests route 100% to the stable target group.
3. **How does this map to AWS infrastructure?**
   - Simulates AWS Route 53 weighted records or ALB target group weights combined with Amazon CloudWatch Alarms triggering an AWS Step Function or Lambda rollback script.

---

## 8. Automated Viva Demonstration Protocol (Phase 13)

To ensure seamless evaluation during academic presentations and live oral examinations, the project includes an automated end-to-end demonstration runner: `backend/scripts/demo_rollback.py`.

### Execution Command
With the FastAPI backend running:

```bash
cd backend
.\venv\Scripts\activate
python scripts/demo_rollback.py
```

### Demonstration Stages and Verification Matrix

| Stage | Action Executed | REST API Route | State Transition | Verification Indicator |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | System Health & JWT Auth | `GET /health`<br>`POST /auth/login` | Unauthenticated -> Authenticated | Bearer JWT generated; Status `200 OK` |
| **Stage 2** | Provision Deployment | `POST /deployments`<br>`POST /deployments/{id}/start` | `PENDING` -> `RUNNING` | Deployment record persisted; Threshold set to `10.0%` |
| **Stage 3** | Pilot Canary Phase | `POST /deployments/{id}/traffic`<br>`POST /deployments/{id}/simulate` | Traffic: `90% Stable / 10% Canary` | 20 client requests dispatched; 0% error rate; Status `RUNNING` |
| **Stage 4** | Expanded Rollout | `POST /deployments/{id}/traffic`<br>`POST /deployments/{id}/simulate` | Traffic: `50% Stable / 50% Canary` | 20 client requests dispatched; Status remains `RUNNING` |
| **Stage 5** | Chaos Fault Injection | `POST /deployments/{id}/failure` | `failure_rate = 0.40`<br>`error_type = HTTP_500` | Audit event `FAILURE_INJECTED` logged |
| **Stage 6** | Automated Circuit Breaker | `POST /deployments/{id}/simulate` | Status: `ROLLED_BACK`<br>Traffic: `100% Stable / 0% Canary` | Monitored error rate > `10.0%`; Immediate traffic restoration |
| **Stage 7** | Forensic Inspection | `GET /deployments/{id}/history`<br>`GET /deployments/{id}/logs` | Forensic Readout | Complete provenance timeline with `AUTO_ROLLBACK` |

### Interactive Dashboard Demonstration (UI Alternative)
Examiners can observe the identical experiment live on the React Web Dashboard:
1. Open `http://localhost:5173`.
2. Navigate to **Architecture & Topology** to inspect the baseline 100% Stable allocation.
3. Select **Traffic Shifting & Simulator**, move the slider to 50/50, click **Apply Traffic Shift**, and simulate 20 requests.
4. Switch to **Chaos & Failure Injection**, select `HTTP 500` or `LATENCY_TIMEOUT`, set the slider to 35%, and click **Inject Fault**.
5. Return to **Traffic Shifting & Simulator** and click **Simulate 30 Requests**.
6. Observe the immediate activation of the glowing red **CIRCUIT BREAKER ACTIVATED** alert banner and verify that traffic weights in the visualizer automatically snap back to 100% Stable.
7. Switch to **Audit Trail & Logs** to review the cryptographic event trail proving automated recovery.

