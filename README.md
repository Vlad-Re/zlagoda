# Zlagoda

A supermarket management system built as a three-tier application:

- **Database** — PostgreSQL (run via Docker Compose)
- **Backend** — Django + Django REST Framework (`backend/`)
- **Frontend** — React 19 + Vite (`frontend/`)

> **Architectural rule:** the backend does **not** use the Django ORM for
> queries — all data access uses raw SQL (`backend/core/db.py`). Tables are
> defined as Django models and created with migrations, but the foreign-key
> **update/delete policies** live in `backend/core/constraints.py` (applied with
> `manage.py apply_constraints`), because the ORM's `on_delete` is bypassed at
> query time and must be enforced at the database level.

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ and npm

## Setup

### 1. Database

Start PostgreSQL:

```bash
docker compose up -d
```

This runs Postgres 15 on `localhost:5433` (host port; the container listens on
5432 internally) with the credentials defined in
`docker-compose.yml` (`admin` / `zlagoda_db`).

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then edit DB_PASSWORD to match docker-compose.yml

python manage.py makemigrations    # generate migrations from core/models.py
python manage.py migrate           # create the tables
python manage.py apply_constraints # apply FK update/delete policies from core/constraints.py
python manage.py runserver         # serves the API on http://localhost:8000
```

Verify it's up:

```bash
curl http://localhost:8000/api/health/
# {"status": "ok", "db": true}
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                        # Vite dev server on http://localhost:5173
```

## Common commands

| Where      | Command                          | Description                              |
| ---------- | -------------------------------- | ---------------------------------------- |
| root       | `docker compose up -d`           | Start PostgreSQL                         |
| root       | `docker compose down`            | Stop PostgreSQL                          |
| `backend`  | `python manage.py makemigrations`   | Generate migrations from `core/models.py` |
| `backend`  | `python manage.py migrate`          | Create the database tables             |
| `backend`  | `python manage.py apply_constraints`| Apply FK update/delete policies        |
| `backend`  | `python manage.py runserver`        | Run the Django API server              |
| `frontend` | `npm run dev`                    | Run the Vite dev server                  |
| `frontend` | `npm run build`                  | Production build                         |
| `frontend` | `npm run lint`                   | Lint the frontend                        |

## Project layout

```
backend/
  config/              Django project (settings, urls, wsgi/asgi)
  core/                the single application
    models.py          table definitions (used only for migrations, not queries)
    db.py              raw-SQL query helpers (fetch_all/fetch_one/execute)
    constraints.py     foreign-key update/delete policies (raw SQL)
    views.py           API endpoints
    urls.py            API routes (mounted under /api/)
    management/commands/apply_constraints.py   applies FK policies to the DB
  manage.py
frontend/              React 19 + Vite app
docker-compose.yml     PostgreSQL service
```
## How to run migration
from backend directory:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py apply_constraints
```

