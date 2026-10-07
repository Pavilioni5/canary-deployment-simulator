"""
Integration test validating the complete End-to-End Demonstration Flow (Phase 13).
Executes the identical 7-stage sequence used for the live viva presentation.
"""
import pytest


def test_complete_demo_lifecycle_and_rollback(client):
    """
    Validates:
    Stage 1: Admin registration/login & token generation
    Stage 2: Deployment creation & lifecycle start
    Stage 3: 90/10 pilot traffic split & healthy simulation
    Stage 4: 50/50 rollout traffic split & healthy simulation
    Stage 5: Chaos failure injection (40% error rate on Canary)
    Stage 6: Circuit breaker trigger upon threshold breach & auto-rollback
    Stage 7: Forensic audit trail and structured log verification
    """
    # -------------------------------------------------------------------------
    # Stage 1: Authentication
    # -------------------------------------------------------------------------
    client.post("/auth/register", json={
        "email": "demo_admin@academic.local",
        "password": "AdminSecurePassword123!",
        "full_name": "Academic Demo Administrator",
        "role": "ADMIN"
    })

    login_res = client.post("/auth/login", json={
        "email": "demo_admin@academic.local",
        "password": "AdminSecurePassword123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------------------
    # Stage 2: Provision Deployment
    # -------------------------------------------------------------------------
    dep_res = client.post(
        "/deployments",
        json={
            "name": "E2E Checkout Pipeline",
            "description": "Validation of full automated rollback lifecycle",
            "rollback_threshold": 10.0,
            "evaluation_window_seconds": 60,
            "stable_tag": "v1.0.0",
            "canary_tag": "v2.0.0",
            "stable_latency_ms": 30.0,
            "canary_latency_ms": 35.0,
            "initial_canary_failure_rate": 0.0
        },
        headers=headers
    )
    assert dep_res.status_code == 201
    dep_id = dep_res.json()["id"]

    # Start deployment
    start_res = client.post(f"/deployments/{dep_id}/start", headers=headers)
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "RUNNING"

    # -------------------------------------------------------------------------
    # Stage 3: Pilot 90/10 Split
    # -------------------------------------------------------------------------
    shift1_res = client.post(
        f"/deployments/{dep_id}/traffic",
        json={"stable_percentage": 90.0, "canary_percentage": 10.0},
        headers=headers
    )
    assert shift1_res.status_code == 200
    assert shift1_res.json()["canary_percentage"] == 10.0

    sim1_res = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 20},
        headers=headers
    )
    assert sim1_res.status_code == 200
    assert sim1_res.json()["status"] == "RUNNING"
    assert sim1_res.json()["triggered_rollback"] is False
    assert sim1_res.json()["canary_summary"]["error_rate"] == 0.0

    # -------------------------------------------------------------------------
    # Stage 4: Expanded 50/50 Split
    # -------------------------------------------------------------------------
    shift2_res = client.post(
        f"/deployments/{dep_id}/traffic",
        json={"stable_percentage": 50.0, "canary_percentage": 50.0},
        headers=headers
    )
    assert shift2_res.status_code == 200
    assert shift2_res.json()["canary_percentage"] == 50.0

    sim2_res = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 20},
        headers=headers
    )
    assert sim2_res.status_code == 200
    assert sim2_res.json()["status"] == "RUNNING"
    assert sim2_res.json()["triggered_rollback"] is False

    # -------------------------------------------------------------------------
    # Stage 5: Inject Controlled Fault (40% error rate on Canary)
    # -------------------------------------------------------------------------
    fail_res = client.post(
        f"/deployments/{dep_id}/failure",
        json={
            "failure_rate": 0.40,
            "error_type": "HTTP_500",
            "affected_version": "CANARY"
        },
        headers=headers
    )
    assert fail_res.status_code == 200
    assert fail_res.json()["failure_rate"] == 0.40
    assert fail_res.json()["status"] == "FAILURE_INJECTED"

    # -------------------------------------------------------------------------
    # Stage 6: Dispatch Traffic, Breach Threshold & Auto-Rollback
    # -------------------------------------------------------------------------
    sim3_res = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 30},
        headers=headers
    )
    assert sim3_res.status_code == 200
    sim3_data = sim3_res.json()

    # Verify circuit breaker execution
    assert sim3_data["triggered_rollback"] is True
    assert sim3_data["status"] == "ROLLED_BACK"
    assert sim3_data["traffic_weights"]["stable"] == 100.0
    assert sim3_data["traffic_weights"]["canary"] == 0.0
    assert "Automatic circuit-breaker rollback triggered" in sim3_data["rollback_reason"]

    # Verify deployment is marked ROLLED_BACK in DB
    dep_check = client.get(f"/deployments/{dep_id}", headers=headers).json()
    assert dep_check["status"] == "ROLLED_BACK"

    # Verify simulation blocked on ROLLED_BACK deployment
    blocked_res = client.post(
        f"/deployments/{dep_id}/simulate",
        json={"count": 10},
        headers=headers
    )
    assert blocked_res.status_code == 400

    # -------------------------------------------------------------------------
    # Stage 7: Forensic Audit Trail & Logs Verification
    # -------------------------------------------------------------------------
    hist_res = client.get(f"/deployments/{dep_id}/history", headers=headers)
    assert hist_res.status_code == 200
    events = hist_res.json()
    event_types = [e["event_type"] for e in events]
    assert "CREATED" in event_types
    assert "TRAFFIC_SHIFT" in event_types
    assert "FAILURE_INJECTED" in event_types
    assert "AUTO_ROLLBACK" in event_types

    log_res = client.get(f"/deployments/{dep_id}/logs", headers=headers)
    assert log_res.status_code == 200
    logs = log_res.json()
    circuit_logs = [l for l in logs if l["source"] == "CIRCUIT_BREAKER" and l["level"] == "CRITICAL"]
    assert len(circuit_logs) > 0
