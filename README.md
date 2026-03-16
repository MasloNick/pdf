# CourtCRM Pro

NPL Portfolio Management System for managing non-performing loan portfolios, court cases, and enforcement proceedings in Ukraine.

## Architecture

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Celery + Redis
- **Frontend**: React 18 / TypeScript / Tailwind CSS / TanStack Table & Query
- **Database**: PostgreSQL 15+ / Redis / SQLite (address DB)
- **AI Parsing**: 3-level hybrid (rules → local LLM → Claude API)

## Quick Start

```bash
# Start all services
docker compose up -d

# Backend only (development)
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend only (development)
cd frontend
npm install
npm run dev
```

## Services

| Service       | Port  | Description                  |
|---------------|-------|------------------------------|
| Backend API   | 8000  | FastAPI REST + WebSocket     |
| Frontend      | 3000  | React dev server             |
| PostgreSQL    | 5432  | Main database                |
| Redis         | 6379  | Celery broker + cache        |

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Legacy

The original Flask address search app is preserved in `/scripts/webapp.py`.
