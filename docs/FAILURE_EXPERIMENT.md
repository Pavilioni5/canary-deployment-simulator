# Controlled Failure Scenario & Automatic Rollback Experiment (P71)

## Objective
Demonstrate controlled failure injection into the Canary release (v2) to validate that automated monitoring detects error rate breaches and immediately rolls back traffic to 100% Stable (v1).

## Experiment Parameters
- **Baseline Stable Version**: v1.0.0 (Failure rate = 0%)
- **Canary Candidate Version**: v2.0.0 (Failure rate configurable: e.g., 30%)
- **Rollback Threshold**: 10.0% Error Rate
- **Batch Size**: 50 to 100 requests per evaluation window

## Execution Flow
1. Deploy canary version at 10% traffic.
2. Verify Canary error rate remains below threshold (healthy state).
3. Increase traffic to 25% or 50%.
4. Trigger `POST /deployments/{id}/failure` with `failure_rate: 0.35` (35%).
5. Simulate 50 requests:
   - Canary receives ~50% of traffic.
   - ~35% of Canary requests fail (HTTP 500 error simulated).
   - Overall or Canary error rate calculated.
6. Observe automated rollback trigger:
   - Status transitions to `ROLLED_BACK`.
   - Traffic routing reset: Stable = 100%, Canary = 0%.
   - Audit event logged with error rate, threshold, timestamp, and root cause.
