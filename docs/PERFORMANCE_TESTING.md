# Load & Scalability Testing Guide (P71)

## Overview
Scalability testing evaluates the response times, throughput, and error rates of the Canary Deployment Simulator under varied concurrent user loads using Locust.

## Test Profiles
1. **Low Workload**:
   - 10 concurrent users
   - Spawn rate: 2 users/sec
   - Duration: 2 minutes
2. **Medium Workload**:
   - 50 concurrent users
   - Spawn rate: 5 users/sec
   - Duration: 3 minutes
3. **High Workload**:
   - 100 concurrent users
   - Spawn rate: 10 users/sec
   - Duration: 5 minutes

## Key Metrics Captured
- Total Request Count
- Requests Per Second (RPS / Throughput)
- Average & 95th Percentile Response Time (ms)
- Failure Count and Failure Percentage (%)
