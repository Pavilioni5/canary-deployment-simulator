"""
Unit and integration tests for Metrics aggregation, Observability Logs, and Deployment History.
"""
import pytest


@pytest.fixture(scope="module")
def setup_metrics_environment(client):
    """Register user, login, and create an active deployment for metrics testing."""
    client.post("/auth/register", json={
        "email": "observability_eng@academic.local",
        "password": "Password123!",
        "full_name": "Observability Engineer",
        "role": "USER"
    })
    token = client.post("/auth/login", json={
        "email": "observability_eng@academic.local",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dep_res = client.post(
        "/deployments",
        json={
            "name": "Telemetry Microservice",
            "description": "Metrics and logging testing",
            "rollback_threshold": 12.0,
            "stable_tag": "v1.0.0",
            "canary_tag": "v2.0.0",
            "stable_latency_ms": 30.0,
            "canary_latency_ms": 35.0,
            "initial_canary_failure_rate": 0.0
        },
        headers=headers
    )
    dep_id = dep_res.json()["id"]

    # Start deployment
    client.post(f"/deployments/{dep_id}/start", headers=headers)

    return {
        "headers": headers,
        "deployment_id": dep_id
    }


def test_get_metrics_initial_state(client, setup_metrics_environment):
    """Verify initial deployment metrics report zero requests and healthy baseline."""
    headers = setup_metrics_environment["headers"]
    dep_id = setup_metrics_environment["deployment_id"]

    response = client.get(f"/deployments/{dep_id}/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["deployment_id"] == dep_id
    assert data["total_requests"] == 0
    assert data["stable_requests"] == 0
    assert data["canary_requests"] == 0
    assert data["overall_error_rate"] == 0.0
    assert data["rollback_count"] == 0
    assert "average_response_time_ms" in data


def test_metrics_populated_after_simulation(client, setup_metrics_environment):
    """Verify simulating traffic records snapshots and aggregates required metrics."""
    headers = setup_metrics_environment["headers"]
    dep_id = setup_metrics_environment["deployment_id"]

    # 1. Shift traffic to 30% Canary / 70% Stable
    client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 30.0, "stable_percentage": 70.0},
        headers=headers
    )

    # 2. Simulate 40 requests
    client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 40},
        headers=headers
    )

    # 3. Query aggregated metrics
    response = client.get(f"/deployments/{dep_id}/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Verify all 6 requested academic metrics
    assert data["total_requests"] == 40
    assert data["stable_requests"] + data["canary_requests"] == 40
    assert data["stable_requests"] > 0
    assert data["canary_requests"] > 0
    assert data["overall_error_rate"] == 0.0
    assert data["average_response_time_ms"] > 0.0
    assert data["rollback_count"] == 0

    # Verify time-series snapshots exist
    assert len(data["recent_snapshots"]) >= 3
    version_types = [s["version_type"] for s in data["recent_snapshots"]]
    assert "STABLE" in version_types
    assert "CANARY" in version_types
    assert "TOTAL" in version_types


def test_get_deployment_logs(client, setup_metrics_environment):
    """Verify diagnostic logs are captured for lifecycle actions and queryable."""
    headers = setup_metrics_environment["headers"]
    dep_id = setup_metrics_environment["deployment_id"]

    response = client.get(f"/deployments/{dep_id}/logs", headers=headers)
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) > 0

    # Verify log entry fields
    sample = logs[0]
    assert "level" in sample
    assert "source" in sample
    assert "message" in sample
    assert "timestamp" in sample

    # Test filtering by level=INFO
    info_response = client.get(f"/deployments/{dep_id}/logs?level=INFO", headers=headers)
    assert info_response.status_code == 200
    for l in info_response.json():
        assert l["level"] == "INFO"


def test_get_deployment_history(client, setup_metrics_environment):
    """Verify chronological audit events track state transitions."""
    headers = setup_metrics_environment["headers"]
    dep_id = setup_metrics_environment["deployment_id"]

    response = client.get(f"/deployments/{dep_id}/history", headers=headers)
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 3

    event_types = [e["event_type"] for e in events]
    assert "CREATED" in event_types
    assert "STARTED" in event_types
    assert "TRAFFIC_SHIFT" in event_types


def test_unauthenticated_metrics_access_rejected(client, setup_metrics_environment):
    """Verify unauthenticated callers cannot query metrics, logs, or history."""
    dep_id = setup_metrics_environment["deployment_id"]
    assert client.get(f"/deployments/{dep_id}/metrics").status_code in [401, 403]
    assert client.get(f"/deployments/{dep_id}/logs").status_code in [401, 403]
    assert client.get(f"/deployments/{dep_id}/history").status_code in [401, 403]
