"""
Unit and integration tests for Automated Circuit Breaker and Manual Rollback mechanisms.
"""
import pytest


@pytest.fixture(scope="module")
def setup_rollback_environment(client):
    """Register user, login, and create an active deployment for rollback testing."""
    client.post("/auth/register", json={
        "email": "rollback_eng@academic.local",
        "password": "Password123!",
        "full_name": "Rollback Test Engineer",
        "role": "USER"
    })
    token = client.post("/auth/login", json={
        "email": "rollback_eng@academic.local",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dep_res = client.post(
        "/deployments",
        json={
            "name": "Payment Rollback Service",
            "description": "Validating automated rollback upon threshold breach",
            "rollback_threshold": 10.0,
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


def test_manual_rollback_resets_traffic_and_status(client, setup_rollback_environment):
    """Verify manual rollback resets traffic to 100/0 and updates status to ROLLED_BACK."""
    headers = setup_rollback_environment["headers"]
    dep_id = setup_rollback_environment["deployment_id"]

    # 1. Shift traffic to 40% Canary
    client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 40.0, "stable_percentage": 60.0},
        headers=headers
    )

    # 2. Trigger manual rollback
    rollback_res = client.post(
        f"/deployments/{dep_id}/rollback",
        json={"reason": "Manual emergency drill"},
        headers=headers
    )
    assert rollback_res.status_code == 200
    data = rollback_res.json()
    assert data["status"] == "ROLLED_BACK"
    assert data["rollback_type"] == "MANUAL"
    assert data["traffic_restored"]["stable"] == 100.0
    assert data["traffic_restored"]["canary"] == 0.0

    # 3. Check traffic config in DB
    traffic_res = client.get(f"/deployments/{dep_id}/traffic", headers=headers)
    assert traffic_res.json()["stable_percentage"] == 100.0
    assert traffic_res.json()["canary_percentage"] == 0.0

    # 4. Check audit events
    history = client.get(f"/deployments/{dep_id}/history", headers=headers).json()
    event_types = [e["event_type"] for e in history]
    assert "MANUAL_ROLLBACK" in event_types


def test_automatic_rollback_triggered_on_threshold_breach(client):
    """
    Verify automatic circuit breaker triggers when Canary error rate exceeds threshold:
    - Status transitions to ROLLED_BACK
    - Traffic is immediately restored to 100% Stable / 0% Canary
    - AUTO_ROLLBACK audit event is created
    - CRITICAL log is written
    - rollback_count is incremented
    """
    # 1. Register distinct user and create deployment with 10% threshold
    client.post("/auth/register", json={
        "email": "circuit_breaker@academic.local",
        "password": "Password123!",
        "full_name": "Circuit Breaker Engineer",
        "role": "USER"
    })
    token = client.post("/auth/login", json={
        "email": "circuit_breaker@academic.local",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dep_res = client.post(
        "/deployments",
        json={
            "name": "Auto Rollback Target",
            "rollback_threshold": 10.0,
            "stable_tag": "v1.0.0",
            "canary_tag": "v2.0.0"
        },
        headers=headers
    )
    dep_id = dep_res.json()["id"]
    client.post(f"/deployments/{dep_id}/start", headers=headers)

    # 2. Inject 100% failure rate into Canary v2
    client.put(
        f"/deployments/{dep_id}/versions/CANARY",
        json={"failure_rate": 1.0},
        headers=headers
    )

    # 3. Shift traffic to 30% Canary / 70% Stable
    client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 30.0, "stable_percentage": 70.0},
        headers=headers
    )

    # 4. Simulate 20 requests
    sim_res = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 20},
        headers=headers
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    # Canary received requests and they failed -> error rate is 100% > 10%
    assert sim_data["canary_summary"]["total_requests"] > 0
    assert sim_data["canary_summary"]["error_rate"] == 100.0
    assert sim_data["triggered_rollback"] is True
    assert "Automatic circuit-breaker rollback triggered" in sim_data["rollback_reason"]
    assert sim_data["status"] == "ROLLED_BACK"
    assert sim_data["traffic_weights"]["stable"] == 100.0
    assert sim_data["traffic_weights"]["canary"] == 0.0

    # 5. Verify database deployment status is ROLLED_BACK
    dep_detail = client.get(f"/deployments/{dep_id}", headers=headers).json()
    assert dep_detail["status"] == "ROLLED_BACK"
    assert dep_detail["traffic_config"]["stable_percentage"] == 100.0
    assert dep_detail["traffic_config"]["canary_percentage"] == 0.0

    # 6. Verify audit history contains AUTO_ROLLBACK
    history = client.get(f"/deployments/{dep_id}/history", headers=headers).json()
    event_types = [e["event_type"] for e in history]
    assert "AUTO_ROLLBACK" in event_types

    # 7. Verify critical log entry
    logs = client.get(f"/deployments/{dep_id}/logs?level=CRITICAL", headers=headers).json()
    assert len(logs) >= 1
    assert "CIRCUIT BREAKER" in logs[0]["message"]

    # 8. Verify metrics reflects rollback_count >= 1
    metrics = client.get(f"/deployments/{dep_id}/metrics", headers=headers).json()
    assert metrics["rollback_count"] >= 1


def test_simulation_blocked_on_rolled_back_deployment(client, setup_rollback_environment):
    """Verify simulating traffic on an already rolled-back deployment returns 400 Bad Request."""
    headers = setup_rollback_environment["headers"]
    dep_id = setup_rollback_environment["deployment_id"]

    # Deployment is in ROLLED_BACK state from first test
    response = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 5},
        headers=headers
    )
    assert response.status_code == 400
    assert "requires deployment status 'RUNNING'" in response.json()["detail"]


def test_unauthenticated_rollback_rejected(client, setup_rollback_environment):
    """Verify unauthenticated requests cannot trigger manual rollbacks."""
    dep_id = setup_rollback_environment["deployment_id"]
    response = client.post(f"/deployments/{dep_id}/rollback")
    assert response.status_code in [401, 403]
