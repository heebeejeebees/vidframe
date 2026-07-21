# Local backend stack (Docker Compose)

This stack runs `backend` + `postgres` + `redis` for durable jobs and dedup cache testing.

## Files

- `deploy/local/docker-compose.backend.yml`
- `deploy/local/.env.compose.example`
- `backend/.env.example`

## Quick start

```bash
cd /Users/ufinity/Documents/Projects/vidframe
cp deploy/local/.env.compose.example deploy/local/.env.compose
cp backend/.env.example backend/.env.local
docker compose --env-file deploy/local/.env.compose -f deploy/local/docker-compose.backend.yml up --build -d
```

## Smoke test

```bash
cd /Users/ufinity/Documents/Projects/vidframe
python3 backend/scripts/smoke_test_local.py
```

## Optional pgAdmin

```bash
cd /Users/ufinity/Documents/Projects/vidframe
docker compose --env-file deploy/local/.env.compose -f deploy/local/docker-compose.backend.yml --profile tools up -d
```

pgAdmin URL: `http://127.0.0.1:5050`

## Stop stack

```bash
cd /Users/ufinity/Documents/Projects/vidframe
docker compose --env-file deploy/local/.env.compose -f deploy/local/docker-compose.backend.yml down
```

