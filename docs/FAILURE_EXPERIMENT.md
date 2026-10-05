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
