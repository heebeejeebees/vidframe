import hashlib
import io
import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

import boto3
import redis
import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from video_processor import VideoClarityProcessor, extract_frame_jpeg

# -- Security & Configuration --

S3_BUCKET = os.getenv("VIDEO_BUCKET_NAME", "")
S3_PREFIX = os.getenv("VIDEO_BUCKET_PREFIX", "vidframe")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "500"))
RECAPTCHA_ENABLED = os.getenv("RECAPTCHA_ENABLED", "false").lower() == "true"
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
UPLOADS_PER_IP_PER_MINUTE = int(os.getenv("UPLOADS_PER_IP_PER_MINUTE", "6"))
UPLOADS_PER_IP_PER_DAY = int(os.getenv("UPLOADS_PER_IP_PER_DAY", "100"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vidframe.db")
REDIS_URL = os.getenv("REDIS_URL", "")
REDIS_DEDUP_TTL_SECONDS = int(os.getenv("REDIS_DEDUP_TTL_SECONDS", "604800"))

REDIS_ANALYSIS_KEY_PREFIX = "vidframe:analysis"

s3_client = boto3.client("s3")
redis_client: Optional[redis.Redis] = None
if REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
    except Exception:
        redis_client = None

# 1. Rate Limiting (Basic DDoS prevention)
# This limits how many requests a single IP can make.
limiter = Limiter(key_func=get_remote_address, default_limits=["180/minute"])

# 2. CORS (Cross-Origin Resource Sharing)
origins_env = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:5173")
origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]

ip_upload_minute: Dict[str, list[float]] = {}
ip_upload_day: Dict[str, list[float]] = {}


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    time_start: Mapped[str] = mapped_column(String(16), nullable=False)
    time_end: Mapped[str] = mapped_column(String(16), nullable=False)

    source_s3_bucket: Mapped[str] = mapped_column(String(256), nullable=False)
    source_s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)

    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_duplicate_source: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    analysis_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_s3_key: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)


class AnalysisRecord(Base):
    __tablename__ = "analysis_cache"

    sha256: Mapped[str] = mapped_column(String(64), primary_key=True)
    analysis_s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


engine_kwargs: Dict[str, Any] = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -- FastAPI App Initialization --

app = FastAPI(title="My Vue3 Backend")

# Add Middleware (Security handlers)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _require_s3_bucket() -> None:
    if not S3_BUCKET:
        raise HTTPException(
            status_code=500,
            detail="VIDEO_BUCKET_NAME is not configured on the backend.",
        )


def _prune_list(values: list[float], window_seconds: int, now: float) -> None:
    keep_from = now - window_seconds
    while values and values[0] < keep_from:
        values.pop(0)


def _enforce_ip_upload_quota(ip_address: str) -> None:
    now = time.time()

    minute_values = ip_upload_minute.setdefault(ip_address, [])
    _prune_list(minute_values, 60, now)
    if len(minute_values) >= UPLOADS_PER_IP_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Too many uploads from this IP in the last minute.",
        )

    day_values = ip_upload_day.setdefault(ip_address, [])
    _prune_list(day_values, 60 * 60 * 24, now)
    if len(day_values) >= UPLOADS_PER_IP_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail="Daily upload limit reached for this IP address.",
        )

    minute_values.append(now)
    day_values.append(now)


def _verify_captcha_or_raise(token: str, remote_ip: str) -> None:
    if not RECAPTCHA_ENABLED:
        return

    if not RECAPTCHA_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="RECAPTCHA_ENABLED is true but RECAPTCHA_SECRET_KEY is missing.",
        )

    if not token:
        raise HTTPException(status_code=400, detail="Missing captcha token.")

    payload = urlencode(
        {
            "secret": RECAPTCHA_SECRET_KEY,
            "response": token,
            "remoteip": remote_ip,
        }
    ).encode("utf-8")
    req = UrlRequest(
        "https://www.google.com/recaptcha/api/siteverify",
        data=payload,
        method="POST",
    )

    try:
        with urlopen(req, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to verify captcha with Google: {exc}",
        )

    if not body.get("success"):
        raise HTTPException(status_code=400, detail="Captcha verification failed.")


def _safe_filename(filename: str) -> str:
    leaf = Path(filename).name
    return leaf.replace("/", "_").replace("\\", "_") or "video.mp4"


def _s3_key(*parts: str) -> str:
    return "/".join([S3_PREFIX.strip("/")] + [part.strip("/") for part in parts if part])


def _analysis_cache_redis_key(sha256_hex: str) -> str:
    return f"{REDIS_ANALYSIS_KEY_PREFIX}:{sha256_hex}"


def _serialize_job(job: JobRecord) -> Dict[str, Any]:
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "filename": job.filename,
        "content_type": job.content_type,
        "size_bytes": job.size_bytes,
        "time_start": job.time_start,
        "time_end": job.time_end,
        "source_s3_bucket": job.source_s3_bucket,
        "source_s3_key": job.source_s3_key,
        "sha256": job.sha256,
        "is_duplicate_source": bool(job.is_duplicate_source),
        "analysis": json.loads(job.analysis_json) if job.analysis_json else None,
        "analysis_s3_key": job.analysis_s3_key,
    }


def _get_job_or_404(job_id: str) -> Dict[str, Any]:
    with get_db() as db:
        job = db.get(JobRecord, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return _serialize_job(job)


def _update_job(job_id: str, **fields: Any) -> None:
    with get_db() as db:
        job = db.get(JobRecord, job_id)
        if not job:
            return

        for key, value in fields.items():
            if key == "analysis":
                setattr(job, "analysis_json", json.dumps(value))
            else:
                setattr(job, key, value)
        job.updated_at = _now_utc()
        db.commit()


def _create_job_record(
    *,
    job_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    time_start: str,
    time_end: str,
    source_s3_bucket: str,
    source_s3_key: str,
    sha256: str,
    is_duplicate_source: bool,
) -> None:
    now = _now_utc()
    with get_db() as db:
        db.add(
            JobRecord(
                job_id=job_id,
                status="queued",
                progress_pct=0,
                error=None,
                created_at=now,
                updated_at=now,
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                time_start=time_start,
                time_end=time_end,
                source_s3_bucket=source_s3_bucket,
                source_s3_key=source_s3_key,
                sha256=sha256,
                is_duplicate_source=is_duplicate_source,
                analysis_json=None,
                analysis_s3_key=None,
            )
        )
        db.commit()


def _cache_analysis_key(sha256_hex: str, analysis_s3_key: str) -> None:
    if not redis_client:
        return
    try:
        redis_client.setex(
            _analysis_cache_redis_key(sha256_hex),
            REDIS_DEDUP_TTL_SECONDS,
            analysis_s3_key,
        )
    except Exception:
        return


def _get_cached_analysis_key(sha256_hex: str) -> Optional[str]:
    if not redis_client:
        return None
    try:
        value = redis_client.get(_analysis_cache_redis_key(sha256_hex))
        return str(value) if value else None
    except Exception:
        return None


def _upsert_analysis_cache_record(sha256_hex: str, analysis_s3_key: str) -> None:
    now = _now_utc()
    with get_db() as db:
        row = db.get(AnalysisRecord, sha256_hex)
        if row:
            row.analysis_s3_key = analysis_s3_key
            row.updated_at = now
        else:
            db.add(
                AnalysisRecord(
                    sha256=sha256_hex,
                    analysis_s3_key=analysis_s3_key,
                    created_at=now,
                    updated_at=now,
                )
            )
        db.commit()


def _get_analysis_key_from_persistent_cache(sha256_hex: str) -> Optional[str]:
    with get_db() as db:
        row = db.get(AnalysisRecord, sha256_hex)
        if row:
            return row.analysis_s3_key
    return None


def _load_analysis_json_from_s3(analysis_s3_key: str) -> Dict[str, Any]:
    result = s3_client.get_object(Bucket=S3_BUCKET, Key=analysis_s3_key)
    return json.loads(result["Body"].read().decode("utf-8"))


def _process_job_video(job_id: str, tmp_path: Path, time_start: str, time_end: str, sha256_hex: str) -> None:
    try:
        _update_job(job_id, status="processing", progress_pct=1, error=None)

        def _on_progress(done: int, total: int) -> None:
            if total <= 0:
                pct = 99
            else:
                pct = min(99, int(done * 100 / total))
            _update_job(job_id, progress_pct=pct)

        processor = VideoClarityProcessor(time_start=time_start, time_end=time_end)
        analysis_result = processor.process(
            str(tmp_path),
            include_bitmap=False,
            progress_callback=_on_progress,
        )

        response_payload = {
            "video": {
                "frames": analysis_result["frames"],
                "fps": analysis_result["fps"],
                "width": analysis_result["width"],
                "height": analysis_result["height"],
            },
            "processing_duration_seconds": analysis_result["duration_seconds"],
            "frames": analysis_result["data"],
        }

        analysis_key = _s3_key("analysis", sha256_hex, "clarity.json")
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=analysis_key,
            Body=json.dumps(response_payload).encode("utf-8"),
            ContentType="application/json",
        )

        _upsert_analysis_cache_record(sha256_hex, analysis_key)
        _cache_analysis_key(sha256_hex, analysis_key)

        _update_job(
            job_id,
            status="done",
            progress_pct=100,
            analysis=response_payload,
            analysis_s3_key=analysis_key,
        )
    except Exception as exc:
        _update_job(job_id, status="failed", error=str(exc))
    finally:
        tmp_path.unlink(missing_ok=True)


# -- API Endpoints --


@app.get("/api/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    return {"status": "ok", "message": "API is running."}


@app.get("/api/config")
@limiter.limit("60/minute")
async def api_config(request: Request):
    return {
        "recaptcha_enabled": RECAPTCHA_ENABLED,
        "max_upload_mb": MAX_UPLOAD_MB,
    }


@app.post("/api/captcha/verify")
@limiter.limit("40/minute")
async def verify_captcha(request: Request, token: str = Form(default="")):
    remote_ip = get_remote_address(request)
    _verify_captcha_or_raise(token, remote_ip)
    return {
        "ok": True,
        "recaptcha_enabled": RECAPTCHA_ENABLED,
        "message": "Captcha accepted." if RECAPTCHA_ENABLED else "Captcha disabled by backend config.",
    }


@app.post("/api/jobs")
@limiter.limit("20/minute")
async def create_job(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    time_start: str = Form(default="00:00"),
    time_end: str = Form(default="00:00"),
    captcha_token: str = Form(default=""),
):
    _require_s3_bucket()

    remote_ip = get_remote_address(request)
    _enforce_ip_upload_quota(remote_ip)
    _verify_captcha_or_raise(captcha_token, remote_ip)

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video files are allowed.")

    tmp_dir = Path("/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    job_id = uuid.uuid4().hex
    safe_name = _safe_filename(file.filename or f"video-{job_id}.mp4")
    tmp_path = tmp_dir / f"{job_id}-{safe_name}"
    sha256_hash = hashlib.sha256()
    size_bytes = 0

    try:
        with tmp_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max upload size is {MAX_UPLOAD_MB} MB.",
                    )
                sha256_hash.update(chunk)
                buffer.write(chunk)
    except HTTPException:
        tmp_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to write temp file: {exc}")
    finally:
        await file.close()

    sha256_hex = sha256_hash.hexdigest()
    source_ext = Path(safe_name).suffix or ".mp4"
    s3_key = _s3_key("videos", sha256_hex, f"source{source_ext}")

    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        is_duplicate = True
    except Exception:
        is_duplicate = False

    if not is_duplicate:
        try:
            s3_client.upload_file(str(tmp_path), S3_BUCKET, s3_key)
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {exc}")

    _create_job_record(
        job_id=job_id,
        filename=safe_name,
        content_type=file.content_type,
        size_bytes=size_bytes,
        time_start=time_start,
        time_end=time_end,
        source_s3_bucket=S3_BUCKET,
        source_s3_key=s3_key,
        sha256=sha256_hex,
        is_duplicate_source=is_duplicate,
    )

    cached_analysis_key = _get_cached_analysis_key(sha256_hex)
    if not cached_analysis_key:
        cached_analysis_key = _get_analysis_key_from_persistent_cache(sha256_hex)
        if cached_analysis_key:
            _cache_analysis_key(sha256_hex, cached_analysis_key)

    if cached_analysis_key:
        _update_job(
            job_id,
            status="done",
            progress_pct=100,
            analysis_s3_key=cached_analysis_key,
        )
        tmp_path.unlink(missing_ok=True)
        return {
            "job_id": job_id,
            "status": "done",
            "progress_pct": 100,
            "is_duplicate_source": is_duplicate,
            "is_duplicate_analysis": True,
        }

    background_tasks.add_task(
        _process_job_video,
        job_id,
        tmp_path,
        time_start,
        time_end,
        sha256_hex,
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "progress_pct": 0,
        "is_duplicate_source": is_duplicate,
        "is_duplicate_analysis": False,
    }


@app.get("/api/jobs/{job_id}")
@limiter.limit("120/minute")
async def get_job_status(request: Request, job_id: str):
    job = _get_job_or_404(job_id)
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress_pct": job["progress_pct"],
        "error": job["error"],
        "filename": job["filename"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "source_s3_bucket": job["source_s3_bucket"],
        "source_s3_key": job["source_s3_key"],
        "is_duplicate_source": job["is_duplicate_source"],
    }


@app.get("/api/jobs/{job_id}/frames")
@limiter.limit("30/minute")
async def get_job_frames(request: Request, job_id: str):
    job = _get_job_or_404(job_id)
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job is not complete yet.")

    analysis = job["analysis"]
    if not analysis:
        if not job["analysis_s3_key"]:
            raise HTTPException(status_code=500, detail="Analysis payload is missing.")
        analysis = _load_analysis_json_from_s3(job["analysis_s3_key"])
        _update_job(job_id, analysis=analysis)

    return {
        "job_id": job["job_id"],
        "analysis": analysis,
    }


@app.get("/api/jobs/{job_id}/frame/{frame_index}")
@limiter.limit("120/minute")
async def get_frame_preview(request: Request, job_id: str, frame_index: int):
    job = _get_job_or_404(job_id)
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job is not complete yet.")

    tmp_path = Path("/tmp") / f"frame-preview-{job_id}-{uuid.uuid4().hex}.bin"
    try:
        s3_client.download_file(job["source_s3_bucket"], job["source_s3_key"], str(tmp_path))
        jpg_bytes = extract_frame_jpeg(str(tmp_path), frame_index)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read frame: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)

    return StreamingResponse(io.BytesIO(jpg_bytes), media_type="image/jpeg")


@app.get("/api/jobs/{job_id}/frame/{frame_index}/download")
@limiter.limit("120/minute")
async def download_frame(request: Request, job_id: str, frame_index: int):
    job = _get_job_or_404(job_id)
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="Job is not complete yet.")

    tmp_path = Path("/tmp") / f"frame-download-{job_id}-{uuid.uuid4().hex}.bin"
    try:
        s3_client.download_file(job["source_s3_bucket"], job["source_s3_key"], str(tmp_path))
        jpg_bytes = extract_frame_jpeg(str(tmp_path), frame_index)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to export frame: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)

    safe_filename = f"vidframe-{job_id}-{frame_index}.jpg"
    headers = {"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    return StreamingResponse(io.BytesIO(jpg_bytes), media_type="image/jpeg", headers=headers)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
