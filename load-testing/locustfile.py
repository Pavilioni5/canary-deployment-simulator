"""
Locust Load & Scalability Testing for Canary Deployment Simulator (P71).
Supports Low (10 users), Medium (50 users), and High (100 users) load profiles.
"""
from locust import HttpUser, task, between
import os


class CanaryTrafficUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Optionally authenticate before running tasks."""
        self.client.headers = {"Content-Type": "application/json"}

    @task(3)
    def test_health_check(self):
        """Simulate frequent health check requests."""
        self.client.get("/health")

    @task(5)
    def test_root_endpoint(self):
        """Simulate root traffic checking system availability."""
        self.client.get("/")
