# CourtCRM Pro v2.0

NPL Portfolio, Court Cases & Enforcement Management System for Ukrainian financial companies.

## Architecture

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Celery + Redis
- **Frontend**: React 18, TypeScript, TanStack Table/Query, Tailwind CSS
- **Database**: PostgreSQL 15+, Redis, SQLite (address DB)
- **AI Parser**: Hybrid — rule-based + local LLM (MamayLM) + Claude API fallback

## Quick Start

### With Docker

```bash
cd docker
docker compose up -d
```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Edit with your settings
alembic upgrade head
uvicorn app.main:app --reload
```

**Celery Worker:**
```bash
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
backend/
  app/
    api/v1/endpoints/   # REST API endpoints
    core/               # Config, security, database
    models/             # SQLAlchemy ORM models
    schemas/            # Pydantic request/response schemas
    services/           # Business logic
    tasks/              # Celery background tasks
    ai_parser/          # Hybrid court decision parser
    utils/              # Export, encryption utilities
  alembic/              # Database migrations
  tests/                # Backend tests
frontend/
  src/
    pages/              # React page components
    services/           # API client
    types/              # TypeScript types
docker/                 # Docker Compose & Dockerfiles
scripts/                # Legacy address/court tools
```

## API Endpoints

- `POST /api/v1/auth/login` — JWT authentication
- `GET/POST /api/v1/portfolios/` — Portfolio CRUD
- `GET/POST /api/v1/debtors/` — Debtor CRUD with search
- `GET/POST /api/v1/court-cases/` — Court case management
- `GET /api/v1/analytics/dashboard` — Dashboard statistics
- `GET /api/v1/analytics/courts` — Court performance stats
- `GET /api/v1/analytics/judges` — Judge performance stats
- `GET /health` — Health check

## Key Features

- Central NPL portfolio database (up to 50,000 debtors)
- AI-powered court decision parsing with confidence scoring
- Automated registry checks (EDR, bankruptcy, enforcement)
- Nightly batch bankruptcy monitoring with alerts
- Court & judge analytics dashboard
- Excel/PDF export with AES-256 encryption
- JWT auth with role-based access control
