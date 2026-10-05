"""
Integration and unit tests for Controlled Failure Injection & Chaos Engineering (Phase 10).
"""
import pytest


@pytest.fixture(scope="module")
def setup_chaos_environment(client):
    """Register user, login, and create an active deployment for failure injection testing."""
    client.post("/auth/register", json={
        "email": "chaos_engineer@academic.local",
        "password": "Password123!",
        "full_name": "Chaos Specialist",
        "role": "USER"
    })
    token = client.post("/auth/login", json={
        "email": "chaos_engineer@academic.local",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dep_res = client.post(
        "/deployments",
        json={
            "name": "Order Checkout Service",
            "description": "Failure injection and chaos experiment",
            "rollback_threshold": 15.0,
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


def test_inject_failure_canary_success(client, setup_chaos_environment):
    """Verify injecting 35% failure rate into Canary updates parameters and audit log."""
    headers = setup_chaos_environment["headers"]
    dep_id = setup_chaos_environment["deployment_id"]

    response = client.post(
        f"/deployments/{dep_id}/failure",
        json={
            "failure_rate": 0.35,
            "error_type": "HTTP_500",
            "affected_version": "CANARY"
        },
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["deployment_id"] == dep_id
    assert data["affected_version"] == "CANARY"
    assert data["version_tag"] == "v2.0.0"
    assert data["failure_rate"] == 0.35
    assert data["failure_percentage"] == 35.0
    assert data["error_type"] == "HTTP_500"
    assert data["status"] == "FAILURE_INJECTED"
    assert "Controlled failure injected" in data["message"]

    # Verify versions endpoint reflects updated rate
    ver_res = client.get(f"/deployments/{dep_id}/versions", headers=headers)
    assert ver_res.status_code == 200
    canary = next(v for v in ver_res.json() if v["version_type"] == "CANARY")
    assert canary["failure_rate"] == 0.35


def test_inject_failure_percentage_normalization(client, setup_chaos_environment):
    """Verify inputting whole percentage numbers (e.g. 40 instead of 0.40) normalizes gracefully."""
    headers = setup_chaos_environment["headers"]
    dep_id = setup_chaos_environment["deployment_id"]

    response = client.post(
        f"/deployments/{dep_id}/failure",
        json={
            "failure_rate": 40.0,
            "error_type": "HTTP_500",
            "affected_version": "CANARY"
        },
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["failure_rate"] == 0.4
    assert data["failure_percentage"] == 40.0


def test_inject_failure_latency_timeout(client, setup_chaos_environment):
    """Verify LATENCY_TIMEOUT profile returns HTTP 504 and elevated latency."""
    headers = setup_chaos_environment["headers"]
    dep_id = setup_chaos_environment["deployment_id"]

    # Inject 100% timeout failure
    inject_res = client.post(
        f"/deployments/{dep_id}/failure",
        json={
            "failure_rate": 1.0,
            "error_type": "LATENCY_TIMEOUT",
            "affected_version": "CANARY"
        },
        headers=headers
    )
    assert inject_res.status_code == 200

    # Simulate request against Canary
    sim_res = client.post(
        f"/deployments/{dep_id}/simulate/version/CANARY",
        json={"count": 3},
        headers=headers
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["failed_requests"] == 3
    for res in sim_data["results"]:
        assert res["status"] == "FAILED"
        assert res["status_code"] == 504
        assert "HTTP 504: Gateway timeout" in res["error_message"]
        assert res["latency_ms"] >= 2500.0


def test_inject_failure_database_error(client, setup_chaos_environment):
    """Verify DATABASE_ERROR fault profile simulates pool connection drops."""
    headers = setup_chaos_environment["headers"]
    dep_id = setup_chaos_environment["deployment_id"]

    inject_res = client.post(
        f"/deployments/{dep_id}/failure",
        json={
            "failure_rate": 1.0,
            "error_type": "DATABASE_ERROR",
            "affected_version": "CANARY"
        },
        headers=headers
    )
    assert inject_res.status_code == 200

    sim_res = client.post(
        f"/deployments/{dep_id}/simulate/version/CANARY",
        json={"count": 2},
        headers=headers
    )
    assert sim_res.status_code == 200
    for res in sim_res.json()["results"]:
        assert res["status"] == "FAILED"
        assert res["status_code"] == 500
        assert "DatabaseConnectionError" in res["error_message"]


def test_failure_injection_audit_trail_and_logging(client, setup_chaos_environment):
    """Verify failure injection records a FAILURE_INJECTED audit event and CHAOS_ENGINE log."""
    headers = setup_chaos_environment["headers"]
    dep_id = setup_chaos_environment["deployment_id"]

    client.post(
        f"/deployments/{dep_id}/failure",
        json={
            "failure_rate": 0.25,
            "error_type": "HTTP_500",
            "affected_version": "CANARY"
        },
        headers=headers
    )

    # Check Audit History
    hist_res = client.get(f"/deployments/{dep_id}/history", headers=headers)
    assert hist_res.status_code == 200
    events = hist_res.json()
    failure_events = [e for e in events if e["event_type"] == "FAILURE_INJECTED"]
    assert len(failure_events) > 0
    assert "Controlled failure injected" in failure_events[0]["message"]

    # Check Logs
    log_res = client.get(f"/deployments/{dep_id}/logs", headers=headers)
    assert log_res.status_code == 200
    logs = log_res.json()
    chaos_logs = [l for l in logs if l["source"] == "CHAOS_ENGINE"]
    assert len(chaos_logs) > 0


def test_clear_failure_injection(client, setup_chaos_environment):
    """Verify DELETE /deployments/{id}/failure resets synthetic failure rate to zero."""
    headers = setup_chaos_environment["headers"]
    dep_id = setup_chaos_environment["deployment_id"]

    del_res = client.delete(f"/deployments/{dep_id}/failure", headers=headers)
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "CLEARED"
    assert del_data["failure_rate"] == 0.0

    # Simulate Canary to confirm healthy responses
    sim_res = client.post(
        f"/deployments/{dep_id}/simulate/version/CANARY",
        json={"count": 5},
        headers=headers
    )
    assert sim_res.status_code == 200
    assert sim_res.json()["successful_requests"] == 5
    assert sim_res.json()["failed_requests"] == 0


def test_failure_injection_triggers_circuit_breaker(client):
    """End-to-end test: Inject failure -> route traffic -> verify auto-rollback to 100/0."""
    # Setup independent deployment for rollback test
    token = client.post("/auth/login", json={
        "email": "chaos_engineer@academic.local",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dep_res = client.post(
        "/deployments",
        json={
            "name": "Payment Gateway Circuit Breaker",
            "rollback_threshold": 10.0,
            "stable_tag": "v1.0.0",
            "canary_tag": "v2.0.0"
        },
        headers=headers
    )
    dep_id = dep_res.json()["id"]
    client.post(f"/deployments/{dep_id}/start", headers=headers)

    # Shift traffic to 50% Stable / 50% Canary
    client.post(
        f"/deployments/{dep_id}/traffic",
        json={"stable_percentage": 50.0, "canary_percentage": 50.0},
        headers=headers
    )

    # Inject 80% failure into Canary
    client.post(
        f"/deployments/{dep_id}/failure",
        json={"failure_rate": 0.80, "error_type": "HTTP_500", "affected_version": "CANARY"},
        headers=headers
    )

    # Route 25 client requests across split
    sim_res = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 25},
        headers=headers
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    # The high failure rate must have triggered the circuit breaker
    assert sim_data["triggered_rollback"] is True
    assert sim_data["status"] == "ROLLED_BACK"
    assert sim_data["traffic_weights"]["stable"] == 100.0
    assert sim_data["traffic_weights"]["canary"] == 0.0

    # Verify deployment is marked ROLLED_BACK in DB
    dep_check = client.get(f"/deployments/{dep_id}", headers=headers).json()
    assert dep_check["status"] == "ROLLED_BACK"


def test_unauthenticated_failure_injection_rejected(client, setup_chaos_environment):
    """Verify unauthorized users cannot inject failures."""
    dep_id = setup_chaos_environment["deployment_id"]
    response = client.post(f"/deployments/{dep_id}/failure", json={"failure_rate": 0.5})
    assert response.status_code in [401, 403]


def test_inject_failure_invalid_version_fails(client, setup_chaos_environment):
    """Verify invalid version types are rejected by schema validator."""
    headers = setup_chaos_environment["headers"]
    dep_id = setup_chaos_environment["deployment_id"]
    response = client.post(
        f"/deployments/{dep_id}/failure",
        json={"failure_rate": 0.5, "affected_version": "PRODUCTION_BETA"},
        headers=headers
    )
    assert response.status_code == 422
