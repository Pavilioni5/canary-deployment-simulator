#!/usr/bin/env python3
"""
Automated Benchmarking Runner for Locust Load Testing (Project P71).
Executes headless tests across Low (10 users), Medium (50 users), and High (100 users) profiles,
parses generated telemetry statistics, and outputs an academic performance summary.
"""

import os
import sys
import time
import csv
import json
import subprocess
import argparse

DEFAULT_HOST = "http://localhost:8000"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

PROFILES = [
    {
        "name": "Low Workload (10 Users)",
        "users": 10,
        "spawn_rate": 2,
        "duration": "15s",
        "csv_prefix": "benchmark_10u"
    },
    {
        "name": "Medium Workload (50 Users)",
        "users": 50,
        "spawn_rate": 5,
        "duration": "15s",
        "csv_prefix": "benchmark_50u"
    },
    {
        "name": "High Workload (100 Users)",
        "users": 100,
        "spawn_rate": 10,
        "duration": "15s",
        "csv_prefix": "benchmark_100u"
    }
]


def ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR, exist_ok=True)


def run_locust_profile(profile: dict, host: str, locustfile: str, python_exe: str):
    prefix = os.path.join(REPORTS_DIR, profile["csv_prefix"])
    cmd = [
        python_exe, "-m", "locust",
        "-f", locustfile,
        "--headless",
        "-u", str(profile["users"]),
        "-r", str(profile["spawn_rate"]),
        "--run-time", profile["duration"],
        "--host", host,
        "--csv", prefix,
        "--only-summary"
    ]
    print(f"\n[*] Executing {profile['name']} - Concurrency: {profile['users']} users, Spawn Rate: {profile['spawn_rate']}/s, Duration: {profile['duration']}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Warning: Locust exited with code {res.returncode}:\n{res.stderr}")
    return prefix + "_stats.csv"


def parse_stats_csv(csv_path: str):
    """Parses Locust _stats.csv to extract aggregated metrics row."""
    if not os.path.exists(csv_path):
        return None

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Name") == "Aggregated":
                req_count = int(row.get("Request Count", 0))
                fail_count = int(row.get("Failure Count", 0))
                rps = float(row.get("Requests/s", 0.0))
                median_ms = float(row.get("50%", row.get("Median Response Time", 0.0)))
                p95_ms = float(row.get("95%", 0.0))
                p99_ms = float(row.get("99%", 0.0))
                fail_pct = round((fail_count / req_count) * 100.0, 2) if req_count > 0 else 0.0
                return {
                    "total_requests": req_count,
                    "failed_requests": fail_count,
                    "failure_rate_pct": fail_pct,
                    "rps": round(rps, 2),
                    "median_ms": round(median_ms, 2),
                    "p95_ms": round(p95_ms, 2),
                    "p99_ms": round(p99_ms, 2),
                }
    return None


def print_comparison_table(results: list):
    print("\n" + "=" * 95)
    print("      CANARY DEPLOYMENT SIMULATOR (P71) - SCALABILITY & CONCURRENCY BENCHMARK SUMMARY      ")
    print("=" * 95)
    header = f"{'Profile':<25} | {'Users':<6} | {'Requests':<9} | {'Throughput (RPS)':<16} | {'Failures':<9} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'p99 (ms)':<9}"
    print(header)
    print("-" * 95)
    for r in results:
        stats = r.get("stats")
        if stats:
            line = (
                f"{r['name']:<25} | "
                f"{r['users']:<6} | "
                f"{stats['total_requests']:<9} | "
                f"{stats['rps']:<16} | "
                f"{stats['failure_rate_pct']}%{'':<3} | "
                f"{stats['median_ms']:<9} | "
                f"{stats['p95_ms']:<9} | "
                f"{stats['p99_ms']:<9}"
            )
        else:
            line = f"{r['name']:<25} | {r['users']:<6} | No Data Recorded"
        print(line)
    print("=" * 95 + "\n")


def main():
    parser = argparse.ArgumentParser(description="P71 Locust Benchmark Automation Runner")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Target backend host (default: {DEFAULT_HOST})")
    parser.add_argument("--profiles", choices=["all", "low", "medium", "high"], default="all", help="Workload profile to run")
    args = parser.parse_args()

    ensure_reports_dir()
    locustfile_path = os.path.join(os.path.dirname(__file__), "locustfile.py")
    python_exe = sys.executable

    selected_profiles = PROFILES
    if args.profiles == "low":
        selected_profiles = [PROFILES[0]]
    elif args.profiles == "medium":
        selected_profiles = [PROFILES[1]]
    elif args.profiles == "high":
        selected_profiles = [PROFILES[2]]

    results = []
    for p in selected_profiles:
        csv_file = run_locust_profile(p, args.host, locustfile_path, python_exe)
        stats = parse_stats_csv(csv_file)
        results.append({
            "name": p["name"],
            "users": p["users"],
            "stats": stats
        })

    print_comparison_table(results)

    # Save JSON summary
    summary_path = os.path.join(REPORTS_DIR, "benchmark_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[*] Benchmark summary persisted to: {summary_path}")


if __name__ == "__main__":
    main()
