# MyCoach

A personal practice tracker with a daily loop: pick life areas, write your own practices, check them off, and see scores that come only from those checks.

The Today note is a short template companion — it reads the same board and does not invent numbers. It is not an AI product yet. See `docs/ai.md` for the future coach contract: interpret the board, never write the board.

Architecture (ERD, APIs, scoring, MVP): see `docs/ARCHITECTURE.md`.

## Phase 1 (this slice)

Register, sign in, choose catalog + custom life areas, add practices, complete a week, follow progress. Secrets, rate limits, Alembic migrations, date bounds, settings, export/delete, and honest charts are in place for a private beta.

## Run locally

```bash
cp .env.example .env
# Set SECRET_KEY to a real value (32+ chars). Example:
#   python3 -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose up -d
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Use the venv binaries (not conda/global alembic):
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:3001

API: http://localhost:8000/docs · Health: http://localhost:8000/health

## Docker

```bash
# Postgres + Redis
docker compose up -d

# API image (runs migrations on start)
docker build -t mycoach-api ./backend
docker run --env-file .env -p 8000:8000 --network host mycoach-api
```

## Tests

```bash
cd backend && source .venv/bin/activate && pytest -q
```

Postgres must be running (docker compose). Tests use a separate `mycoach_test` database on port **5433**.
