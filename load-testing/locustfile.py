"""
Locust Scalability & Load Testing Suite for Canary Deployment Simulator (P71).

Evaluates system throughput (RPS), response latency distributions (p50, p95, p99),
and stability across low (10 users), medium (50 users), and high (100 users) concurrency profiles.
"""

import json
import logging
from locust import HttpUser, task, between, events

logger = logging.getLogger("locust.canary")

ADMIN_EMAIL = "admin@canary.local"
ADMIN_PASSWORD = "AdminSecurePassword123!"


class CanarySimulatorUser(HttpUser):
    """
    Simulates concurrent client operators and automated monitoring agents
    interacting with the Canary Deployment Simulator REST API.
    """
    # Think time between requests (100ms to 800ms)
    wait_time = between(0.1, 0.8)

    def on_start(self):
        """Authenticates user session and discovers/provisions target deployment."""
        self.token = None
        self.deployment_id = 1

        # 1. Authenticate with FastAPI Backend
        login_res = self.client.post(
            "/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            name="/auth/login"
        )
        if login_res.status_code == 200:
            self.token = login_res.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            # Fallback: register load test user
            reg_res = self.client.post(
                "/auth/register",
                json={
                    "email": "loadtester@academic.local",
                    "password": "Password123!",
                    "full_name": "Locust Load Tester",
                    "role": "ADMIN"
                },
                name="/auth/register"
            )
            login2 = self.client.post(
                "/auth/login",
                json={"email": "loadtester@academic.local", "password": "Password123!"},
                name="/auth/login"
            )
            if login2.status_code == 200:
                self.token = login2.json().get("access_token")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})

        # 2. Discover active deployments or seed a benchmark deployment
        deps_res = self.client.get("/deployments", name="/deployments")
        if deps_res.status_code == 200:
            deps = deps_res.json()
            if deps:
                # Find a running or pending deployment
                running = [d for d in deps if d["status"] in ["RUNNING", "PENDING"]]
                if running:
                    self.deployment_id = running[0]["id"]
                    if running[0]["status"] == "PENDING":
                        self.client.post(f"/deployments/{self.deployment_id}/start", name="/deployments/[id]/start")
                else:
                    self.deployment_id = deps[0]["id"]
            else:
                # Create benchmark deployment
                created = self.client.post(
                    "/deployments",
                    json={
                        "name": "Benchmark Canary Service",
                        "description": "Locust Scalability Workload Target",
                        "rollback_threshold": 15.0,
                        "evaluation_window_seconds": 60,
                        "stable_tag": "v1.0.0",
                        "canary_tag": "v2.0.0",
                        "stable_latency_ms": 10.0,
                        "canary_latency_ms": 15.0,
                        "initial_canary_failure_rate": 0.0
                    },
                    name="/deployments"
                )
                if created.status_code == 201:
                    self.deployment_id = created.json()["id"]
                    self.client.post(f"/deployments/{self.deployment_id}/start", name="/deployments/[id]/start")

    # -------------------------------------------------------------------------
    # High-Frequency Task: Dispatched Routed Client Traffic (Weight 10)
    # -------------------------------------------------------------------------
    @task(10)
    def simulate_routed_traffic(self):
        """Simulate client requests passing through the weighted ALB target groups."""
        self.client.post(
            f"/deployments/{self.deployment_id}/simulate",
            json={"count": 5},
            name="/deployments/[id]/simulate"
        )

    # -------------------------------------------------------------------------
    # Telemetry Polling: Real-Time Metrics Telemetry (Weight 6)
    # -------------------------------------------------------------------------
    @task(6)
    def fetch_metrics(self):
        """Simulate frontend dashboard polling aggregated metrics snapshots."""
        self.client.get(
            f"/deployments/{self.deployment_id}/metrics",
            name="/deployments/[id]/metrics"
        )

    # -------------------------------------------------------------------------
    # Health Probe: Load Balancer Liveness Check (Weight 4)
    # -------------------------------------------------------------------------
    @task(4)
    def check_liveness(self):
        """Simulate infrastructure health probe checking gateway availability."""
        self.client.get("/health", name="/health")

    # -------------------------------------------------------------------------
    # Observability: Fetch Structured Diagnostic Logs (Weight 2)
    # -------------------------------------------------------------------------
    @task(2)
    def fetch_logs(self):
        """Simulate log viewer inspecting recent application logs."""
        self.client.get(
            f"/deployments/{self.deployment_id}/logs?limit=20",
            name="/deployments/[id]/logs"
        )

    # -------------------------------------------------------------------------
    # Audit Trail: Fetch Lifecycle Event Provenance (Weight 2)
    # -------------------------------------------------------------------------
    @task(2)
    def fetch_history(self):
        """Simulate operator querying deployment lifecycle audit history."""
        self.client.get(
            f"/deployments/{self.deployment_id}/history",
            name="/deployments/[id]/history"
        )

    # -------------------------------------------------------------------------
    # Fleet Query: Inspect Deployment Versions & Status (Weight 1)
    # -------------------------------------------------------------------------
    @task(1)
    def fetch_version_details(self):
        """Simulate inspecting target group version parameters."""
        self.client.get(
            f"/deployments/{self.deployment_id}/versions",
            name="/deployments/[id]/versions"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("Starting Locust Scalability & Concurrency Benchmark for Project P71...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Locust Scalability Benchmark completed. Analyzing response statistics.")
