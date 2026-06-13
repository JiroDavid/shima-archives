# ShimaVault Backend

FastAPI service: Twitch API proxy, VOD / clip / chat endpoints, and the RAG chatbot query API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # fill in Twitch + API credentials
```

## Run

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- All routes are versioned under `/api/v1`.

## Database migrations (Alembic)

`DATABASE_URL` is read from `.env`. With Postgres running:

```bash
alembic revision --autogenerate -m "create initial tables"
alembic upgrade head
```

## Tests / lint / types

```bash
pytest
ruff check .
mypy app
```

## Layout

```
app/
├── core/        config (pydantic-settings)
├── db/          engine, session, declarative Base
├── models/      SQLAlchemy models (channels, vods, chat_messages, streamers)
├── schemas/     Pydantic request/response shapes
├── routers/     API v1 endpoints
├── services/    Twitch client, RAG pipeline
└── main.py      FastAPI app
alembic/         migration environment
tests/           pytest suite
```

Endpoints currently return `501 Not Implemented` until each is built out — see
`docs/PROGRESS.md` for the order of work.
