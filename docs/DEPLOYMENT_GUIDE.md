# Deployment & Execution Guide (P71)

## Local Development Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Docker and Docker Compose (recommended) or local PostgreSQL / SQLite

### 2. Environment Setup
```bash
cp .env.example .env
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 5. Running with Docker Compose
```bash
docker compose up --build
```
