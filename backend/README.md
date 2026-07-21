# vidframe backend

FastAPI backend that accepts video uploads, stores originals in S3, computes per-frame clarity scores, and exposes polling + frame export endpoints.

## Environment variables

Create `backend/.env` (or export in shell):

- `VIDEO_BUCKET_NAME` (required)
- `VIDEO_BUCKET_PREFIX` (default: `vidframe`)
- `CORS_ORIGINS` (comma-separated, default: `http://localhost:8080,http://localhost:5173`)
- `DATABASE_URL` (default: `sqlite:///./vidframe.db`)
- `REDIS_URL` (optional but recommended for dedup scale-out)
- `REDIS_DEDUP_TTL_SECONDS` (default: `604800`)
- `MAX_UPLOAD_MB` (default: `500`)
- `UPLOADS_PER_IP_PER_MINUTE` (default: `6`)
- `UPLOADS_PER_IP_PER_DAY` (default: `100`)
- `RECAPTCHA_ENABLED` (`true` or `false`, default: `false`)
- `RECAPTCHA_SECRET_KEY` (required only when recaptcha enabled)
- AWS credentials via instance profile / env vars

## Run locally

```bash
cd /Users/ufinity/Documents/Projects/vidframe/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Run with Docker (Postgres + Redis)

Use the local stack in `deploy/local` for durable-job testing:

```bash
cd /Users/ufinity/Documents/Projects/vidframe
cp deploy/local/.env.compose.example deploy/local/.env.compose
cp backend/.env.example backend/.env.local
docker compose --env-file deploy/local/.env.compose -f deploy/local/docker-compose.backend.yml up --build -d
python3 backend/scripts/smoke_test_local.py
```

Stop it with:

```bash
cd /Users/ufinity/Documents/Projects/vidframe
docker compose --env-file deploy/local/.env.compose -f deploy/local/docker-compose.backend.yml down
```

## API overview

- `GET /api/health`
- `GET /api/config`
- `POST /api/captcha/verify` (form field: `token`)
- `POST /api/jobs` (multipart fields: `file`, `time_start`, `time_end`, `captcha_token`)
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/frames`
- `GET /api/jobs/{job_id}/frame/{frame_index}`
- `GET /api/jobs/{job_id}/frame/{frame_index}/download`

## Upload + processing flow

1. Frontend uploads file to `POST /api/jobs`.
2. Backend writes a temp file, computes SHA-256, uploads source to S3 key:
   - `VIDEO_BUCKET_PREFIX/videos/{sha256}/source.ext`
3. If that SHA has already been analyzed (Redis cache + persistent table), the job is returned as `done` immediately.
4. Otherwise a background task runs OpenCV clarity processing.
5. Frontend polls `GET /api/jobs/{job_id}` until `status` is `done`.
6. Frontend loads points with `GET /api/jobs/{job_id}/frames`.
7. Frame preview/download calls fetch the selected frame from source video.

## Notes

- Job storage is persisted in `jobs` table and dedup pointers are persisted in `analysis_cache`.
- Redis is used as an optional fast cache layer for dedup lookup; system falls back to DB when Redis is unavailable.
- Rate limiting is enforced by `slowapi` and additional per-IP upload quotas.
