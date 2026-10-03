"""
Unit and integration tests for Deployment CRUD REST APIs, version generation, and lifecycle states.
"""
import pytest


@pytest.fixture(scope="module")
def auth_tokens(client):
    """Register and authenticate test users (User A, User B, and Admin)."""
    # 1. Register User A
    client.post("/auth/register", json={
        "email": "developer_a@academic.local",
        "password": "Password123!",
        "full_name": "Developer A",
        "role": "USER"
    })
    token_a = client.post("/auth/login", json={
        "email": "developer_a@academic.local",
        "password": "Password123!"
    }).json()["access_token"]

    # 2. Register User B
    client.post("/auth/register", json={
        "email": "developer_b@academic.local",
        "password": "Password123!",
        "full_name": "Developer B",
        "role": "USER"
    })
    token_b = client.post("/auth/login", json={
        "email": "developer_b@academic.local",
        "password": "Password123!"
    }).json()["access_token"]

    # 3. Register Admin
    client.post("/auth/register", json={
        "email": "super_admin@academic.local",
        "password": "AdminPassword123!",
        "full_name": "Super Admin",
        "role": "ADMIN"
    })
    token_admin = client.post("/auth/login", json={
        "email": "super_admin@academic.local",
        "password": "AdminPassword123!"
    }).json()["access_token"]

    return {
        "user_a": token_a,
        "user_b": token_b,
        "admin": token_admin
    }


def test_create_deployment_success(client, auth_tokens):
    """Verify creating a deployment initializes stable/canary versions and 100/0 traffic."""
    token = auth_tokens["user_a"]
    payload = {
        "name": "Order Checkout Service",
        "description": "Production canary rollout testing",
        "rollback_threshold": 10.0,
        "evaluation_window_seconds": 60,
        "stable_tag": "v1.0.0",
        "canary_tag": "v2.0.0",
        "stable_latency_ms": 40.0,
        "canary_latency_ms": 45.0,
        "initial_canary_failure_rate": 0.0
    }
    response = client.post(
        "/deployments",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Order Checkout Service"
    assert data["status"] == "PENDING"
    assert data["rollback_threshold"] == 10.0
    assert len(data["versions"]) == 2

    # Check version types
    types = [v["version_type"] for v in data["versions"]]
    assert "STABLE" in types
    assert "CANARY" in types

    # Check initial traffic distribution (100% stable, 0% canary)
    assert data["traffic_config"]["stable_percentage"] == 100.0
    assert data["traffic_config"]["canary_percentage"] == 0.0


def test_create_deployment_unauthenticated_fails(client):
    """Verify unauthorized requests cannot create deployments."""
    response = client.post("/deployments", json={"name": "Rogue Service"})
    assert response.status_code in [401, 403]


def test_list_deployments_isolation(client, auth_tokens):
    """Verify users only see their own deployments while admins see all."""
    token_a = auth_tokens["user_a"]
    token_b = auth_tokens["user_b"]
    token_admin = auth_tokens["admin"]

    # User B creates a deployment
    client.post(
        "/deployments",
        json={"name": "User B Billing App", "rollback_threshold": 12.0},
        headers={"Authorization": f"Bearer {token_b}"}
    )

    # User A lists deployments -> should not see User B's deployment
    res_a = client.get("/deployments", headers={"Authorization": f"Bearer {token_a}"})
    names_a = [d["name"] for d in res_a.json()]
    assert "Order Checkout Service" in names_a
    assert "User B Billing App" not in names_a

    # Admin lists deployments -> sees both
    res_admin = client.get("/deployments", headers={"Authorization": f"Bearer {token_admin}"})
    names_admin = [d["name"] for d in res_admin.json()]
    assert "Order Checkout Service" in names_admin
    assert "User B Billing App" in names_admin


def test_get_deployment_by_id(client, auth_tokens):
    """Verify retrieving deployment by ID includes version and traffic sub-objects."""
    token_a = auth_tokens["user_a"]
    deployments = client.get("/deployments", headers={"Authorization": f"Bearer {token_a}"}).json()
    dep_id = deployments[0]["id"]

    response = client.get(f"/deployments/{dep_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dep_id
    assert "versions" in data
    assert "traffic_config" in data


def test_update_deployment_threshold(client, auth_tokens):
    """Verify updating deployment settings persists modified values."""
    token_a = auth_tokens["user_a"]
    deployments = client.get("/deployments", headers={"Authorization": f"Bearer {token_a}"}).json()
    dep_id = deployments[0]["id"]

    response = client.put(
        f"/deployments/{dep_id}",
        json={"rollback_threshold": 15.0, "description": "Updated threshold to 15%"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 200
    assert response.json()["rollback_threshold"] == 15.0


def test_start_deployment_lifecycle(client, auth_tokens):
    """Verify starting a deployment moves status from PENDING to RUNNING."""
    token_a = auth_tokens["user_a"]
    deployments = client.get("/deployments", headers={"Authorization": f"Bearer {token_a}"}).json()
    dep_id = deployments[0]["id"]

    response = client.post(
        f"/deployments/{dep_id}/start",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"


def test_delete_deployment_and_cascade(client, auth_tokens):
    """Verify deleting a deployment removes the record and cascaded versions."""
    token_b = auth_tokens["user_b"]
    deployments = client.get("/deployments", headers={"Authorization": f"Bearer {token_b}"}).json()
    dep_id = deployments[0]["id"]

    # Delete deployment
    delete_res = client.delete(f"/deployments/{dep_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert delete_res.status_code == 204

    # Subsequent GET returns 404
    get_res = client.get(f"/deployments/{dep_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_res.status_code == 404
