# Database Design & Justification (P71)

## Why PostgreSQL?
1. **Relational Integrity**: Canary deployments involve interconnected entities (deployments, version configurations, routing stages, metric records, and audit logs). Foreign key constraints ensure data consistency.
2. **ACID Transaction Support**: Atomic rollback events require synchronous updates across traffic configs, deployment status, and audit logs.
3. **Structured Time-Series Metric Querying**: SQL allows indexed querying of historical metrics over moving evaluation windows.
4. **Cloud / RDS Compatibility**: Directly maps to AWS RDS PostgreSQL or Aurora in enterprise environments.

## Schema Entities
- `users`: ID, email, hashed_password, full_name, role (ADMIN/USER), created_at.
- `deployments`: ID, name, status (PENDING, RUNNING, COMPLETED, ROLLED_BACK), user_id, rollback_threshold, created_at.
- `deployment_versions`: ID, deployment_id, version_name, version_tag (e.g., v1.0.0, v2.0.0), is_canary, failure_rate, created_at.
- `traffic_configs`: ID, deployment_id, stable_percentage, canary_percentage, updated_at.
- `metrics`: ID, deployment_id, total_requests, successful_requests, failed_requests, error_rate, avg_latency_ms, recorded_at.
- `deployment_events`: ID, deployment_id, event_type (TRAFFIC_SHIFT, FAILURE_INJECTED, AUTO_ROLLBACK, MANUAL_ROLLBACK), details, timestamp.
- `logs`: ID, deployment_id, level (INFO, WARN, ERROR), message, timestamp.
