# Cloud-Based Canary Deployment Simulator

**Project ID**: P71  
**Course**: Cloud Computing / Final Year Academic Project  
**Author**: B.Tech Student  

---

## Project Overview

Canary deployment is a deployment strategy that reduces the risk of introducing a new software version into production by gradually shifting incoming traffic from a stable version to a candidate version.

This project implements a complete, self-contained Canary Deployment Simulator. It models how traffic can be incrementally routed from a baseline stable release (v1) to a canary release (v2), monitors real-time health metrics (request count, success count, failure count, error rate, and response latency), and initiates an automatic rollback to 100% stable traffic whenever the canary error rate breaches a predefined failure threshold.

The simulator provides an interactive backend REST API with automated unit and integration tests, database persistence using PostgreSQL and SQLAlchemy, role-based JWT authentication, configurable failure injection, and containerized deployment support.

---

## Objectives

1. Demonstrate dynamic traffic shifting between two application versions (e.g., 90/10, 75/25, 50/50, 0/100).
2. Emulate realistic network latency and stochastic failure behavior in microservices.
3. Automatically detect service degradation and trigger immediate circuit-breaker rollback to protect user experience.
4. Maintain a persistent audit trail of all traffic adjustments, failure events, and system logs.
5. Provide a testable, cost-effective architecture suitable for academic demonstration, load testing, and viva evaluation.

---

## System Architecture

```text
                           +---------------------------+
                           |  React Dashboard (Vite)   |
                           +-------------+-------------+
                                         | HTTP / REST (Bearer JWT)
                                         v
                           +---------------------------+
                           |   FastAPI REST Backend    |
                           +-------------+-------------+
                                         |
                         +---------------+---------------+
                         |                               |
                         v                               v
            +-------------------------+     +-------------------------+
            |  Traffic Split Router   |     |  Rollback & Health Unit |
            +------------+------------+     +------------+------------+
                         |                               ^
                 +-------+-------+                       | Monitors Error Rate
                 |               |                       |
                 v               v                       |
           +-----------+   +-----------+                 |
           | Stable v1 |   | Canary v2 | ----------------+
           +-----+-----+   +-----+-----+
                 |               |
                 +-------+-------+
                         |
                         v
           +---------------------------+
           |   PostgreSQL / SQLite     |
           |  - Deployments & Versions |
           |  - Metrics & Telemetry    |
           |  - Audit Events & Logs    |
           +---------------------------+
```

### Architectural Components
- **Client Tier**: Web-based monitoring dashboard communicating over authenticated REST endpoints.
- **API and Routing Layer**: FastAPI service that manages authentication, coordinates traffic distribution, and serves as an Application Load Balancer (ALB) abstraction.
- **Application Instances**: Concurrent simulated instances representing Stable (v1) and Canary (v2) workloads with distinct latency profiles and configurable failure rates.
- **Health and Rollback Controller**: Automated monitoring routine comparing sliding-window error rates against the configured threshold.
- **Data Persistence**: Relational storage (PostgreSQL in production/Docker, SQLite option for local testing) managed through SQLAlchemy ORM.

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18, Vite | Interactive metrics and control dashboard |
| Backend | Python 3.10+, FastAPI | REST API engine, routing logic, and OpenAPI documentation |
| Database | PostgreSQL 15, SQLAlchemy ORM | Relational schema, transaction management, and time-series metrics |
| Security | JWT (PyJWT), Bcrypt | Stateless token authentication and salted password hashing |
| Testing | Pytest, HTTPX | Automated unit, integration, and API contract tests |
| Load Testing | Locust | Concurrency benchmarking at 10, 50, and 100 user workloads |
| Containers | Docker, Docker Compose | Multi-container local orchestration (db, backend, frontend) |
| Cloud Alignment | AWS-compatible patterns | Emulates EC2 compute, RDS PostgreSQL, and ALB target group routing |

---

## Repository Structure

```text
canary-deployment-simulator/
|-- backend/
|   |-- app/
|   |   |-- auth/               # JWT token utilities, password hashing, and RBAC dependencies
|   |   |-- models/             # SQLAlchemy ORM definitions (users, deployments, metrics, logs)
|   |   |-- routes/             # REST endpoint routers (health, auth, deployments, simulation)
|   |   |-- schemas/            # Pydantic validation models
|   |   |-- services/           # Business logic for deployment lifecycle and version simulation
|   |   |-- utils/              # Database initialization and admin seeding scripts
|   |   |-- config.py           # Environment variables loader
|   |   |-- database.py         # Database engine and session factory
|   |   `-- main.py             # FastAPI entry point and middleware configuration
|   |-- scripts/
|   |   `-- demo_rollback.py    # Automated end-to-end viva rollback demonstration runner
|   |-- tests/                  # Pytest automated test suite (53 test cases)
|   |-- Dockerfile              # Backend container build instructions
|   `-- requirements.txt        # Python dependency manifest
|
|-- frontend/
|   |-- src/
|   |   |-- components/         # Reusable UI widgets
|   |   |-- pages/              # Dashboard view and telemetry panels
|   |   |-- services/           # API client integrations
|   |   |-- App.jsx             # Main application layout
|   |   `-- index.css           # Styling rules
|   |-- package.json            # Node.js dependencies and build scripts
|   `-- Dockerfile              # Multi-stage frontend container build
|
|-- load-testing/
|   |-- locustfile.py           # Load testing scenarios for Locust
|   |-- run_load_test.py        # Headless automated benchmark runner (10, 50, 100 users)
|   `-- requirements.txt        # Locust dependencies manifest
|
|-- docs/
|   |-- API_DOCUMENTATION.md    # REST API specification with request and response examples
|   |-- ARCHITECTURE.md         # System design details and Mermaid sequence flows
|   |-- DATABASE_DESIGN.md      # Schema definitions, ER diagram, and PostgreSQL justification
|   |-- DEPLOYMENT_GUIDE.md     # Setup instructions for local and containerized execution
|   |-- FAILURE_EXPERIMENT.md   # Step-by-step controlled failure injection lab
|   |-- PERFORMANCE_TESTING.md  # Low, medium, and high workload test protocols
|   `-- VIVA_GUIDE.md           # Examiner questions, explanations, and live modifications
|
|-- docker-compose.yml          # Container configuration for local development
|-- .env.example                # Template of environment variables
|-- .gitignore                  # Git exclusion rules
`-- README.md                   # Project overview and setup instructions
```

---

## Setup and Installation

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (for frontend)
- Docker and Docker Compose (optional for local containerized execution)

### 1. Environment Configuration
Clone the repository and copy the environment template:
```bash
git clone <repository-url>
cd canary-deployment-simulator
cp .env.example .env
```

### 2. Backend Setup (Local)
Create a Python virtual environment and install dependencies:
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate

pip install -r requirements.txt
python -m app.utils.init_db
uvicorn app.main:app --reload --port 8000
```
The backend API and documentation will be accessible at:
- Root info: http://localhost:8000/
- Interactive Swagger documentation: http://localhost:8000/docs
- Alternative ReDoc interface: http://localhost:8000/redoc

### 3. Frontend Setup (Local)
In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
The user interface will be accessible at http://localhost:5173/.

### 4. Running with Docker Compose
To launch the full stack (PostgreSQL, backend API, and frontend) using Docker:
```bash
docker compose up --build
```

---

## Automated Testing and Demonstration

The backend includes a comprehensive Pytest test suite with 53 automated tests covering health probes, database models, JWT authentication, RBAC authorization, deployment CRUD, version simulation, weighted traffic distribution, real-time metrics telemetry, automated/manual circuit breaker rollbacks, controlled failure injection, and the complete end-to-end demonstration lifecycle.

To execute the test suite:
```bash
cd backend
.\venv\Scripts\activate
pytest -v
```

To execute the automated end-to-end viva demonstration script:
```bash
cd backend
.\venv\Scripts\activate
python scripts/demo_rollback.py
```


---

## Academic Documentation References

Detailed technical documentation is maintained under the `docs/` directory:
- [API Documentation](docs/API_DOCUMENTATION.md): Endpoint specifications and status codes.
- [Architecture Details](docs/ARCHITECTURE.md): Structural breakdown and Mermaid flow diagrams.
- [Database Design](docs/DATABASE_DESIGN.md): Table schemas, indexing strategy, and design justification.
- [Failure Experiment](docs/FAILURE_EXPERIMENT.md): Controlled failure scenario and automatic rollback reproducibility.
- [Performance Testing](docs/PERFORMANCE_TESTING.md): Load profiles at 10, 50, and 100 concurrent users.
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md): Step-by-step local and cloud run instructions.
- [Viva and Oral Exam Guide](docs/VIVA_GUIDE.md): Core concepts, oral questions, and live examiner modifications.
