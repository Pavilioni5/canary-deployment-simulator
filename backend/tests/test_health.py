"""
Unit and integration tests for System & Health check endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns system metadata and project ID P71."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "P71"
    assert data["status"] == "operational"
    assert "version" in data
    assert "environment" in data
    assert data["docs_url"] == "/docs"


def test_health_check_endpoint():
    """Verify liveness probe returns healthy status and uptime."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0.0
    assert "timestamp" in data


def test_detailed_health_endpoint():
    """Verify detailed diagnostics report component statuses."""
    response = client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "api" in data["components"]
    assert data["components"]["api"]["status"] == "healthy"
    assert "database_configured" in data["components"]
    assert "traffic_router" in data["components"]


def test_openapi_documentation_accessible():
    """Verify OpenAPI JSON schema and Swagger docs are generated properly."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Cloud-Based Canary Deployment Simulator"
    assert "paths" in schema
    assert "/health" in schema["paths"]
    assert "/health/details" in schema["paths"]
