# Cloud-Based Canary Deployment Simulator

**Project ID**: P71  
**Domain**: Cloud Computing / DevOps Engineering  
**Academic Context**: B.Tech Final Year Academic Project  

---

## 📌 Project Overview
The **Cloud-Based Canary Deployment Simulator** is an interactive, cloud-ready software engineering tool designed to demonstrate modern zero-downtime deployment patterns. It showcases how live production traffic can be gradually shifted from a baseline stable release (v1) to a candidate canary release (v2) while continuously evaluating application health and error rates.

If the canary version exceeds a configured failure threshold (e.g., error rate > 10%), the system triggers an **automated rollback**, immediately restoring 100% of user traffic to the stable version and recording detailed diagnostic metrics.

---

## 🏗️ Architecture & Component Flow

```
                   +---------------------------+
                   |  React + Vite Dashboard   |
                   +-------------+-------------+
                                 | HTTP / REST (JWT Auth)
                                 v
                   +---------------------------+
                   |     FastAPI Backend       |
                   +-------------+-------------+
                                 |
                 +---------------+---------------+
                 |                               |
                 v                               v
    +-------------------------+     +-------------------------+
    |   Traffic Split Router  |     |  Rollback & Health Unit |
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
   | PostgreSQL Database (RDS) |
   |  - Deployments & Versions |
   |  - Real-time Metrics      |
   |  - Audit Logs & Events    |
   +---------------------------+
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Lucide Icons, Pure CSS (Dark Mode Design System) |
| **Backend** | Python 3.10+, FastAPI (Asynchronous REST API, OpenAPI/Swagger) |
| **Database** | PostgreSQL 15, SQLAlchemy ORM, Alembic migrations ready |
| **Authentication** | JWT (JSON Web Tokens) with PBKDF2/Bcrypt password hashing and RBAC |
| **Testing** | Pytest (Unit & Integration), Locust (Scalability & Load Profiles) |
| **Containerization** | Docker, Docker Compose |
| **Cloud Alignment** | AWS Architecture (EC2/ECS, RDS, ALB, CloudWatch logging patterns) |

---

## 📁 Repository Structure

```
canary-deployment-simulator/
|
|-- backend/
|   |-- app/
|   |   |-- auth/          # JWT authentication and RBAC
|   |   |-- models/        # SQLAlchemy database entity models
|   |   |-- routes/        # REST API endpoints
|   |   |-- schemas/       # Pydantic data validation schemas
|   |   |-- services/      # Canary traffic routing & rollback engine
|   |   |-- utils/         # Helper functions & structured logger
|   |   |-- config.py      # App settings & environment loader
|   |   |-- database.py    # Database connection & session manager
|   |   `-- main.py        # FastAPI application bootstrap
|   |-- tests/             # Automated Pytest test suite
|   |-- Dockerfile         # Backend container definition
|   `-- requirements.txt   # Python dependency specifications
|
|-- frontend/
|   |-- src/
|   |   |-- components/    # Reusable UI widgets & traffic controls
|   |   |-- pages/         # Dashboard & metrics views
|   |   |-- services/      # Axios API client integrations
|   |   |-- App.jsx        # Root application layout
|   |   |-- index.css      # Modern dark-mode styling tokens
|   |   `-- main.jsx       # DOM entry point
|   |-- index.html         # Single Page Application HTML shell
|   |-- package.json       # Frontend dependencies & scripts
|   |-- vite.config.js     # Vite bundler configuration
|   `-- Dockerfile         # Multi-stage production container
|
|-- load-testing/
|   `-- locustfile.py      # Locust stress & scalability scenarios
|
|-- docs/
|   |-- API_DOCUMENTATION.md   # Detailed REST API endpoint specification
|   |-- ARCHITECTURE.md        # Deep-dive cloud architecture & Mermaid flow
|   |-- DATABASE_DESIGN.md     # Relational schema & PostgreSQL justification
|   |-- DEPLOYMENT_GUIDE.md    # Local and container deployment instructions
|   |-- FAILURE_EXPERIMENT.md  # Controlled failure & automated rollback lab
|   |-- PERFORMANCE_TESTING.md # 10, 50, 100 user load test protocol
|   `-- VIVA_GUIDE.md          # Viva questions, answers & live modification tips
|
|-- .env.example           # Environment configuration template
|-- .gitignore             # Standard exclusion rules for secrets and builds
|-- docker-compose.yml     # Multi-container local stack orchestration
`-- README.md              # Project root documentation
```

---

## 🚀 Quick Start Instructions

### 1. Clone & Set Environment
```bash
git clone <repo-url>
cd canary-deployment-simulator
cp .env.example .env
```

### 2. Run with Docker Compose
```bash
docker compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API & Swagger: `http://localhost:8000/docs`

---

## 🎓 Academic Requirements Compliance Checklist
- [x] Clear modular repository structure
- [x] Structured documentation folder (`docs/`)
- [x] Security-first `.env.example` without exposed secrets
- [x] PostgreSQL + SQLAlchemy persistence architecture
- [x] Phase-wise development roadmap
