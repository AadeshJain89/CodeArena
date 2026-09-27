# CodeArena - Programming Practice Platform

CodeArena is a modern web-based programming practice platform featuring user authentication, problem set challenges, Docker-isolated code execution, diagnostic skill assessment, user profiles, a weighted personalized recommendation engine (SLRE), performance analytics, and gamification.

> **Current Phase:** Initial Project Foundation (Module 1)

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** Plain CSS / CSS Variables (No external UI frameworks)

### Backend
- **Framework:** FastAPI (Python 3.12)
- **ORM & DB Tools:** SQLAlchemy 2.x, Alembic
- **Validation:** Pydantic v2 & Pydantic-Settings
- **Async DB Driver:** Asyncpg & Psycopg2

### Database & Caching
- **Primary Database:** PostgreSQL 16
- **Caching & Queueing:** Redis 7

### Infrastructure
- **Containerization:** Docker & Docker Compose

---

## 📁 Repository Structure

```text
CodeArena/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── db.py
│   │   │   └── redis.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── .env.example
│   └── .env
│
├── docker/
│   └── README.md
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### 1. Start PostgreSQL and Redis Containers

Run Docker Compose from the project root:

```bash
docker compose up -d
```

Verify that the containers are healthy and running:

```bash
docker compose ps
```

### 2. Start the FastAPI Backend

Navigate to the `backend` directory, create a virtual environment, install dependencies, and launch Uvicorn:

```bash
cd backend

# Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch FastAPI development server
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- **Health Check Endpoint:** `http://localhost:8000/health`
- **Swagger Documentation:** `http://localhost:8000/docs`

### 3. Start the React Frontend

In a separate terminal, navigate to the `frontend` directory, install dependencies, and start Vite:

```bash
cd frontend

# Install Node modules
npm install

# Start Vite dev server
npm run dev
```

The web application will be accessible at `http://localhost:5173`.

---

## 🚦 Current Implementation Status

- [x] Directory structure setup
- [x] Docker Compose configuration for PostgreSQL & Redis
- [x] FastAPI base application with `/health` endpoint
- [x] SQLAlchemy 2.x async engine & session setup
- [x] Alembic migration framework initialization
- [x] Redis async client configuration
- [x] React + Vite frontend with plain CSS design system
- [x] Environment variable configuration templates (`.env.example`)
- [ ] *Module 2: User Authentication & Roles (USER / ADMIN)* (Upcoming)
- [ ] *Module 3: Problem Management & Test Cases* (Upcoming)
- [ ] *Module 4: Isolated Docker Execution Sandbox* (Upcoming)
- [ ] *Module 5: Diagnostic Assessment & Skill Profiles* (Upcoming)
- [ ] *Module 6: SLRE Recommendation System & Analytics* (Upcoming)
