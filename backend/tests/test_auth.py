"""
Unit and integration tests for JWT authentication, password hashing, and RBAC authorization.
"""
from app.config import settings


def test_register_new_user_success(client):
    """Verify new user registration with hashed password and role assignment."""
    payload = {
        "email": "student@academic.local",
        "password": "StudentPassword123!",
        "full_name": "Academic Student",
        "role": "USER"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student@academic.local"
    assert data["role"] == "USER"
    assert data["is_active"] is True
    assert "hashed_password" not in data  # Sensitive hash must never be returned


def test_register_duplicate_email_fails(client):
    """Verify registering with an existing email returns 400 Bad Request."""
    payload = {
        "email": "student@academic.local",
        "password": "AnotherPassword123!"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_valid_credentials_returns_jwt(client):
    """Verify login authenticates credentials and returns valid JWT access token."""
    login_payload = {
        "email": "student@academic.local",
        "password": "StudentPassword123!"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "student@academic.local"
    assert data["role"] == "USER"
    assert data["expires_in_minutes"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES


def test_login_invalid_password_fails(client):
    """Verify login with incorrect password returns 401 Unauthorized."""
    login_payload = {
        "email": "student@academic.local",
        "password": "WrongPassword!"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_protected_route_without_token_fails(client):
    """Verify protected routes reject unauthenticated requests with 401/403."""
    response = client.get("/auth/me")
    assert response.status_code in [401, 403]


def test_protected_route_with_valid_token(client):
    """Verify /auth/me returns current user identity with valid Bearer token."""
    login_res = client.post("/auth/login", json={
        "email": "student@academic.local",
        "password": "StudentPassword123!"
    })
    token = login_res.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == "student@academic.local"
    assert profile["role"] == "USER"


def test_rbac_admin_endpoint_behavior(client):
    """Verify RBAC: standard user is denied (403), admin user is permitted (200)."""
    # 1. Login as standard user
    user_token = client.post("/auth/login", json={
        "email": "student@academic.local",
        "password": "StudentPassword123!"
    }).json()["access_token"]

    # 2. Standard user tries to access /auth/admin-only -> Expected: 403 Forbidden
    user_res = client.get(
        "/auth/admin-only",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert user_res.status_code == 403
    assert "Operation not permitted" in user_res.json()["detail"]

    # 3. Register and login as an Admin user
    admin_register_payload = {
        "email": "admin_test@academic.local",
        "password": "AdminSecurePassword123!",
        "full_name": "Test Admin",
        "role": "ADMIN"
    }
    client.post("/auth/register", json=admin_register_payload)

    admin_login_res = client.post("/auth/login", json={
        "email": "admin_test@academic.local",
        "password": "AdminSecurePassword123!"
    })
    assert admin_login_res.status_code == 200
    admin_token = admin_login_res.json()["access_token"]

    # 4. Admin accesses /auth/admin-only -> Expected: 200 OK
    admin_res = client.get(
        "/auth/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["role"] == "ADMIN"
