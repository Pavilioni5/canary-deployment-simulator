"""
Unit and integration tests for Stable (v1) and Canary (v2) simulation execution.
"""
import pytest


@pytest.fixture(scope="module")
def setup_sim_environment(client):
    """Register user, login, and create an active deployment for simulation testing."""
    client.post("/auth/register", json={
        "email": "simulator_dev@academic.local",
        "password": "Password123!",
        "full_name": "Simulation Engineer",
        "role": "USER"
    })
    token = client.post("/auth/login", json={
        "email": "simulator_dev@academic.local",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dep_res = client.post(
        "/deployments",
        json={
            "name": "Auth Microservice",
            "description": "Simulation evaluation",
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


def test_simulate_stable_v1_zero_failure(client, setup_sim_environment):
    """Verify Stable v1 with 0% failure rate yields 100% success and HTTP 200 results."""
    headers = setup_sim_environment["headers"]
    dep_id = setup_sim_environment["deployment_id"]

    response = client.post(
        f"/deployments/{dep_id}/simulate/version/STABLE",
        json={"count": 10, "payload": {"action": "verify_token"}},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version_type"] == "STABLE"
    assert data["version_tag"] == "v1.0.0"
    assert data["total_requests"] == 10
    assert data["successful_requests"] == 10
    assert data["failed_requests"] == 0
    assert data["error_rate"] == 0.0
    assert data["avg_latency_ms"] > 0.0
    assert len(data["results"]) == 10

    # Inspect first result
    first = data["results"][0]
    assert first["status"] == "SUCCESS"
    assert first["status_code"] == 200
    assert "X-Amzn-Trace-Id" in first["headers"]
    assert first["headers"]["X-App-Version"] == "v1.0.0"


def test_simulate_canary_v2_with_injected_failures(client, setup_sim_environment):
    """Verify Canary v2 with 100% failure rate correctly produces HTTP 500 error packets."""
    headers = setup_sim_environment["headers"]
    dep_id = setup_sim_environment["deployment_id"]

    # Set canary failure rate to 1.0 (100% failure)
    update_res = client.put(
        f"/deployments/{dep_id}/versions/CANARY",
        json={"failure_rate": 1.0, "simulated_latency_ms": 60.0},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["failure_rate"] == 1.0

    # Simulate 5 requests to Canary v2
    response = client.post(
        f"/deployments/{dep_id}/simulate/version/CANARY",
        json={"count": 5},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version_type"] == "CANARY"
    assert data["version_tag"] == "v2.0.0"
    assert data["total_requests"] == 5
    assert data["successful_requests"] == 0
    assert data["failed_requests"] == 5
    assert data["error_rate"] == 100.0

    # Check error details in results
    for item in data["results"]:
        assert item["status"] == "FAILED"
        assert item["status_code"] == 500
        assert "Simulated HTTP 500" in item["error_message"]
        assert item["headers"]["X-App-Version"] == "v2.0.0"


def test_get_deployment_versions(client, setup_sim_environment):
    """Verify retrieving versions lists both Stable v1 and Canary v2 with active configs."""
    headers = setup_sim_environment["headers"]
    dep_id = setup_sim_environment["deployment_id"]

    response = client.get(f"/deployments/{dep_id}/versions", headers=headers)
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2
    types = [v["version_type"] for v in versions]
    assert "STABLE" in types
    assert "CANARY" in types


def test_simulate_invalid_version_type_fails(client, setup_sim_environment):
    """Verify dispatching requests to invalid version type returns 400 Bad Request."""
    headers = setup_sim_environment["headers"]
    dep_id = setup_sim_environment["deployment_id"]

    response = client.post(
        f"/deployments/{dep_id}/simulate/version/EXPERIMENTAL",
        json={"count": 1},
        headers=headers
    )
    assert response.status_code == 400
    assert "Allowed values: 'STABLE' or 'CANARY'" in response.json()["detail"]


def test_unauthenticated_simulation_fails(client, setup_sim_environment):
    """Verify unauthorized simulation requests are rejected."""
    dep_id = setup_sim_environment["deployment_id"]
    response = client.post(f"/deployments/{dep_id}/simulate/version/STABLE", json={"count": 1})
    assert response.status_code in [401, 403]
