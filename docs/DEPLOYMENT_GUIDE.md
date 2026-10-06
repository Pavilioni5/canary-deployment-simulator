# Deployment and Execution Guide (Project ID: P71)

## 1. Overview

This document provides complete instructions for executing the Cloud-Based Canary Deployment Simulator across three operational modes:
1. **Multi-Container Stack**: Docker and Docker Compose (recommended for full architecture validation and academic viva demonstration).
2. **Hybrid Development Mode**: Containerized PostgreSQL with locally running FastAPI and Vite instances.
3. **Local Lightweight Mode**: Self-contained SQLite database with local Python and Node runtimes (zero-dependency fallback).

---

## 2. Containerized Architecture (Docker Compose)

The multi-container stack orchestrates three discrete services on an isolated Docker bridge network:

```text
               +--------------------------------------------------+
               |                  Docker Host                     |
               |                                                  |
   Port 5173   |   +-------------------+                          |
 ------------> |   |  canary_frontend  |                          |
               |   |   (React/Nginx)   |                          |
               |   +---------+---------+                          |
               |             |                                    |
               |             | HTTP REST                          |
               |             v                                    |
   Port 8000   |   +-------------------+   Database URL           |
 ------------> |   |  canary_backend   | --------------------+    |
               |   |     (FastAPI)     |                     |    |
               |   +-------------------+                     |    |
               |                                             v    |
   Port 5432   |                                   +-------------+|
 ------------> |                                   | canary_db   ||
               |                                   | (PostgreSQL)||
               |                                   +-------------+|
               |                                         |        |
               |                         Volume: postgres_data   |
               +--------------------------------------------------+
```

### Container Specifications

| Container Name | Base Image | Internal Port | Exposed Host Port | Health Check Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| `canary_postgres` | `postgres:15-alpine` | 5432 | `5432:5432` | `pg_isready -U canary_user -d canary_db` |
| `canary_backend` | `python:3.11-slim` | 8000 | `8000:8000` | `curl -f http://localhost:8000/health` |
| `canary_frontend` | `nginx:alpine` | 80 | `5173:80` | `wget -qO- http://localhost/` |

---

## 3. Prerequisites

- **Docker Desktop** (Engine 20.10+ and Compose v2+) OR **Docker Engine** on Linux.
- Minimum hardware resources: 2 GB available RAM, 5 GB disk storage.
- Ports `5432`, `8000`, and `5173` free from local process bindings.

---

## 4. Multi-Container Execution (Option A - Recommended)

### Step 1: Environment Setup
Copy the environment variables template into your active environment configuration:

```bash
cp .env.example .env
```

### Step 2: Build and Start Containers
From the root repository directory:

```bash
docker compose up --build -d
```

### Step 3: Verify Container Health
Check that all three services achieve `healthy` status:

```bash
docker compose ps
```

**Expected Output**:
```text
NAME                IMAGE                                COMMAND                  SERVICE             CREATED             STATUS                        PORTS
canary_postgres     postgres:15-alpine                   "docker-entrypoint.s…"   db                  About a minute ago   Up About a minute (healthy)   0.0.0.0:5432->5432/tcp
canary_backend      canary-deployment-simulator-backend  "uvicorn app.main:ap…"   backend             About a minute ago   Up About a minute (healthy)   0.0.0.0:8000->8000/tcp
canary_frontend     canary-deployment-simulator-frontend "nginx -g 'daemon of…"   frontend            About a minute ago   Up 45 seconds (healthy)       0.0.0.0:5173->80/tcp
```

### Step 4: Access System Interfaces
- **Interactive Web Dashboard**: `http://localhost:5173`
- **Backend Swagger UI**: `http://localhost:8000/docs`
- **Backend ReDoc**: `http://localhost:8000/redoc`
- **Health Check Endpoint**: `http://localhost:8000/health`

---

## 5. Container Lifecycle Management Commands

### Viewing Real-Time Logs
Stream logs from the FastAPI backend:
```bash
docker compose logs -f backend
```

Stream logs from all services concurrently:
```bash
docker compose logs -f
```

### Inspecting PostgreSQL Database
Open an interactive `psql` shell inside the database container:
```bash
docker compose exec db psql -U canary_user -d canary_db
```

List application tables:
```sql
\dt
SELECT id, name, status, rollback_threshold FROM deployments;
SELECT event_type, message, timestamp FROM deployment_events ORDER BY timestamp DESC LIMIT 5;
\q
```

### Stopping the Stack
Stop containers while preserving database volume data:
```bash
docker compose down
```

Stop containers and wipe database volumes (clean reset):
```bash
docker compose down -v
```

---

## 6. Hybrid Development Mode (Option B)

In this mode, PostgreSQL runs inside Docker, while the backend and frontend execute directly on the host machine for live code debugging.

### Step 1: Launch Database Only
```bash
docker compose up -d db
```

### Step 2: Start Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate      # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
python -m app.utils.init_db
uvicorn app.main:app --reload --port 8000
```

### Step 3: Start Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 7. Local Lightweight Mode (Option C - Zero Docker Fallback)

If Docker is unavailable on the test machine, the application can run using SQLite:

1. In `backend/.env`, set:
   ```ini
   DATABASE_URL=sqlite:///./canary_simulator.db
   ```
2. Initialize and start backend:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.utils.init_db
   uvicorn app.main:app --reload --port 8000
   ```
3. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

---

## 8. Troubleshooting & Common Issues

### Port 5432 Already in Use
If a local PostgreSQL service is running on the host machine:
- Modify `ports` in `docker-compose.yml`:
  ```yaml
  ports:
    - "5433:5432"
  ```
- Or stop the local Postgres service before starting Docker Compose.

### SPA 404 on Page Reload
Single-page React applications handle routing in the client browser. The included `frontend/nginx.conf` solves this by directing all unknown paths to `/index.html`:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Backend Fails Database Connection on Startup
In `docker-compose.yml`, the backend service declares:
```yaml
depends_on:
  db:
    condition: service_healthy
```
This guarantees the backend only initializes after PostgreSQL has successfully completed internal socket configuration and reports healthy to `pg_isready`.
