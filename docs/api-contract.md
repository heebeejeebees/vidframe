# API contract (frontend <-> backend)

## Base URL

- Local: `http://127.0.0.1:8000`
- Frontend env key: `VUE_APP_API_BASE_URL`

## 0) Backend runtime config

`GET /api/config`

Response:

```json
{
  "recaptcha_enabled": true,
  "max_upload_mb": 500
}
```

Frontend uses this to decide whether captcha must be completed before upload.

## 1) Create processing job

`POST /api/jobs` (multipart/form-data)

Fields:
- `file` (video file)
- `time_start` (`MM:SS`, optional, default `00:00`)
- `time_end` (`MM:SS`, optional, default `00:00` for full video)
- `captcha_token` (optional unless backend enforces recaptcha)

Response:

```json
{
  "job_id": "7f1...",
  "status": "queued",
  "progress_pct": 0,
  "is_duplicate_source": false,
  "is_duplicate_analysis": false
}
```

## 2) Poll job status

`GET /api/jobs/{job_id}`

Response fields:
- `status`: `queued | processing | done | failed`
- `progress_pct`: 0-100
- `error`: string or null
- source metadata + timestamps

## 3) Fetch analysis points

`GET /api/jobs/{job_id}/frames`

Response:

```json
{
  "job_id": "7f1...",
  "analysis": {
    "video": {
      "frames": 1234,
      "fps": 29.97,
      "width": 1920,
      "height": 1080
    },
    "processing_duration_seconds": 4.52,
    "frames": [
      {
        "index": 35,
        "laplacian_variance": 248.1,
        "timestamp": "00:01"
      }
    ]
  }
}
```

## 4) Frame preview + download

- Preview image: `GET /api/jobs/{job_id}/frame/{frame_index}`
- Download image: `GET /api/jobs/{job_id}/frame/{frame_index}/download`

Both return JPEG image bytes.

## Error semantics

- `400`: invalid input, unsupported file, failed captcha
- `409`: job exists but not complete for frame/frames endpoint
- `413`: file too large
- `429`: IP limits or API rate limit exceeded
- `500/502`: backend/service error


