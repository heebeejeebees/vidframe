import os
import uuid
from pathlib import Path

import boto3
import uvicorn
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from video_processor import VideoClarityProcessor

# -- Security & Configuration --

S3_BUCKET = os.getenv("VIDEO_BUCKET_NAME", "your-video-bucket-name")
S3_PREFIX = os.getenv("VIDEO_BUCKET_PREFIX", "uploads/")

s3_client = boto3.client("s3")

# 1. Rate Limiting (Basic DDoS prevention)
# This limits how many requests a single IP can make.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# 2. CORS (Cross-Origin Resource Sharing)
# This defines which frontend domains are allowed to access this backend.
# IMPORTANT: Change this to your Vue app's actual domain in production.
origins = [
    "http://localhost:5173",  # Vite's default dev server
    "http://localhost:8080",  # Vue CLI's default dev server
    # "https://your-production-vue-app.com" # Add your production domain here
]

# -- FastAPI App Initialization --

app = FastAPI(title="My Vue3 Backend")

# Add Middleware (Security handlers)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# -- API Endpoints --


@app.get("/api/health")
@limiter.limit("10/minute")  # Stricter limit for this specific endpoint
async def health_check(request: Request):
    """
    A simple endpoint to verify the API is running and reachable.
    """
    return {"status": "ok", "message": "API is running! 🚀"}


@app.post("/api/upload")
@limiter.limit("15/minute")  # Limit file uploads to 15 per minute per IP
async def upload_file(
        request: Request,
        file: UploadFile = File(...),
        time_start: str = "00:00",
        time_end: str = "00:00",):
    """
    Accepts a file upload from the frontend, stores it in S3,
    runs clarity analysis, and returns structured data.
    """
    # Basic file validation
    if not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400, detail="Only video files are allowed.")

    # 1) Save to a temporary local path
    tmp_dir = Path("/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    unique_id = uuid.uuid4().hex
    safe_name = file.filename or f"video-{unique_id}.mp4"
    tmp_path = tmp_dir / f"{unique_id}-{safe_name}"

    try:
        with tmp_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write temp file: {e}")

    # 2) Upload to S3
    s3_key = f"{S3_PREFIX}{unique_id}/{safe_name}"

    try:
        s3_client.upload_file(str(tmp_path), S3_BUCKET, s3_key)
    except Exception as e:
        # clean temp file
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to upload to S3: {e}")

    # 3) Process the video locally using OpenCV
    try:
        processor = VideoClarityProcessor(
            time_start=time_start, time_end=time_end)
        analysis_result = processor.process(
            str(tmp_path), include_bitmap=False)
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500, detail=f"Video processing failed: {e}")
    finally:
        # 4) Housekeeping – remove temp file
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    # 5) Return response with analysis + S3 info
    return {
        "filename": safe_name,
        "content_type": file.content_type,
        "s3_bucket": S3_BUCKET,
        "s3_key": s3_key,
        "message": "File uploaded and processed successfully! 📂",
        "analysis": analysis_result,
    }

# -- Running the App --

if __name__ == "__main__":
    # This block allows running the server directly with `python main.py`
    # For production, use Gunicorn (see scalability section).
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
