# Academic Viva & Examination Guide (P71)

## Core Conceptual Questions

### 1. What is Canary Deployment?
A deployment pattern where a new version of software is rolled out to a small percentage of users (canary) alongside the stable version. Metrics are monitored before rolling it out to 100% of the user base.

### 2. Why use Canary Deployment over Blue-Green Deployment?
- **Blue-Green**: Instant switchover between two identical full-scale environments. If a subtle bug exists, 100% of users are immediately exposed.
- **Canary**: Gradual risk minimization. Only 5-10% of users encounter the candidate build, giving automated monitors time to catch regressions and roll back before widespread impact.

### 3. How does the Automated Rollback mechanism work in this simulator?
1. Requests are dynamically routed according to the configured traffic weights.
2. The health monitor calculates the sliding-window error rate: `error_rate = (failed_requests / total_requests) * 100%`.
3. If `canary_error_rate > rollback_threshold`, an automated circuit trigger resets traffic to 100% Stable (v1) and logs a critical event.

## Likely Examiner Live Modifications
1. Change the rollback threshold from 10% to 5% or 20%.
2. Adjust traffic increments (e.g., jump directly from 10% to 50%).
3. Inspect database audit logs for proof of automatic rollback.
