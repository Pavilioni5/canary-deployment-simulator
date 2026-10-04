"""
Unit and integration tests for Traffic Shifting and Weighted Router Simulation.
"""
import pytest


@pytest.fixture(scope="module")
def setup_traffic_environment(client):
    """Register user, login, and create an active deployment for traffic testing."""
    client.post("/auth/register", json={
        "email": "traffic_engineer@academic.local",
        "password": "Password123!",
        "full_name": "Traffic Engineer",
        "role": "USER"
    })
    token = client.post("/auth/login", json={
        "email": "traffic_engineer@academic.local",
        "password": "Password123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dep_res = client.post(
        "/deployments",
        json={
            "name": "Cart Service",
            "description": "Traffic splitting test",
            "rollback_threshold": 15.0,
            "stable_tag": "v1.0.0",
            "canary_tag": "v2.0.0",
            "stable_latency_ms": 25.0,
            "canary_latency_ms": 28.0,
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


def test_shift_traffic_valid_percentage(client, setup_traffic_environment):
    """Verify shifting traffic to 10% Canary / 90% Stable updates configuration."""
    headers = setup_traffic_environment["headers"]
    dep_id = setup_traffic_environment["deployment_id"]

    response = client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 10.0, "stable_percentage": 90.0},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["canary_percentage"] == 10.0
    assert data["stable_percentage"] == 90.0
    assert "successfully updated" in data["message"]


def test_shift_traffic_auto_computes_stable_percentage(client, setup_traffic_environment):
    """Verify omitting stable_percentage automatically computes (100 - canary_percentage)."""
    headers = setup_traffic_environment["headers"]
    dep_id = setup_traffic_environment["deployment_id"]

    response = client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 25.0},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["canary_percentage"] == 25.0
    assert data["stable_percentage"] == 75.0


def test_shift_traffic_invalid_sum_fails(client, setup_traffic_environment):
    """Verify specifying percentages that do not sum to 100% returns 422 validation error."""
    headers = setup_traffic_environment["headers"]
    dep_id = setup_traffic_environment["deployment_id"]

    response = client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 30.0, "stable_percentage": 80.0},
        headers=headers
    )
    assert response.status_code == 422


def test_simulate_traffic_zero_canary_routes_all_to_stable(client, setup_traffic_environment):
    """Verify 0% Canary / 100% Stable routes 100% of client requests to Stable v1."""
    headers = setup_traffic_environment["headers"]
    dep_id = setup_traffic_environment["deployment_id"]

    # Set 0% canary
    client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 0.0, "stable_percentage": 100.0},
        headers=headers
    )

    response = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 20},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 20
    assert data["stable_summary"]["total_requests"] == 20
    assert data["canary_summary"]["total_requests"] == 0


def test_simulate_traffic_hundred_canary_routes_all_to_canary(client, setup_traffic_environment):
    """Verify 100% Canary / 0% Stable routes 100% of client requests to Canary v2."""
    headers = setup_traffic_environment["headers"]
    dep_id = setup_traffic_environment["deployment_id"]

    # Set 100% canary
    client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 100.0, "stable_percentage": 0.0},
        headers=headers
    )

    response = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 15},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 15
    assert data["canary_summary"]["total_requests"] == 15
    assert data["stable_summary"]["total_requests"] == 0


def test_simulate_traffic_fifty_fifty_distribution(client, setup_traffic_environment):
    """Verify 50/50 split distributes traffic to both Stable and Canary within statistical bounds."""
    headers = setup_traffic_environment["headers"]
    dep_id = setup_traffic_environment["deployment_id"]

    # Set 50% split
    client.post(
        f"/deployments/{dep_id}/traffic",
        json={"canary_percentage": 50.0, "stable_percentage": 50.0},
        headers=headers
    )

    response = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 100},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 100

    canary_count = data["canary_summary"]["total_requests"]
    stable_count = data["stable_summary"]["total_requests"]
    assert canary_count + stable_count == 100

    # For 100 samples at p=0.5, both should receive between 30 and 70 requests
    assert 30 <= canary_count <= 70
    assert 30 <= stable_count <= 70

    # Verify routing headers in results
    first_result = data["results"][0]
    assert "X-Canary-Routing" in first_result["headers"]
    assert first_result["headers"]["X-Configured-Canary-Weight"] == "50.0%"


def test_simulate_traffic_unauthenticated_fails(client, setup_traffic_environment):
    """Verify unauthenticated traffic simulation requests are rejected."""
    dep_id = setup_traffic_environment["deployment_id"]
    response = client.post(f"/deployments/{dep_id}/simulate", json={"count": 5})
    assert response.status_code in [401, 403]
