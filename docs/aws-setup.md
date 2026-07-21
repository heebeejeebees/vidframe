# AWS setup guide (minimal cost first)

This guide starts with a low-cost single-host design, then shows how to scale.

## Target architecture (phase 1)

- 1 x EC2 instance (t3.small or t3.medium)
- 1 x S3 bucket for uploaded videos + analysis JSON
- Route53 + ACM + ALB optional later
- CloudWatch metrics/logs
- Security groups restricted to web ports

This gives simple operations and low monthly baseline.

## 1) Create S3 bucket

1. Open S3 -> Create bucket (globally unique name).
2. Disable public access (keep private).
3. Enable default encryption (SSE-S3).
4. Add lifecycle rules:
   - Transition old objects to Glacier Instant Retrieval (optional).
   - Expire temporary derivatives later when your cleanup worker exists.

Suggested key structure:
- `vidframe/videos/{sha256}/source.ext`
- `vidframe/analysis/{sha256}/clarity.json`

## 2) Create IAM roles

### EC2 instance role

Attach policy with least privilege for your bucket:
- `s3:GetObject`
- `s3:PutObject`
- `s3:ListBucket`
- `s3:HeadObject`

Scope resources to your bucket ARN and `vidframe/*` prefix.

### Optional admin user (local deploy)

Use temporary credentials (or SSO) for deployment only.

## 3) Launch EC2

- AMI: Amazon Linux 2023 or Ubuntu 24.04
- Size: t3.small start point
- Disk: 30-50 GB gp3
- Security group:
  - 22 from your IP
  - 80/443 from public

Install runtime and reverse proxy.

## 4) Deploy backend and frontend

- Backend runs as systemd service (`uvicorn` or gunicorn+uvicorn workers).
- Frontend builds static files and can be served by Nginx on same EC2.
- Set backend env vars:
  - `VIDEO_BUCKET_NAME`
  - `VIDEO_BUCKET_PREFIX=vidframe`
  - `CORS_ORIGINS=https://your-domain`
  - `DATABASE_URL` (SQLite for MVP, PostgreSQL/RDS for production)
  - `REDIS_URL` (for fast dedup cache)
  - upload + recaptcha limits

Use the in-repo deployment templates:
- `deploy/ec2/systemd/vidframe-backend.service`
- `deploy/ec2/nginx/vidframe.conf`
- `deploy/ec2/env/backend.redis-db.env.example`
- `deploy/ec2/env/frontend.env.example`
- `deploy/ec2/README.md`

## 5) HTTPS and domain

### Cheapest quick path

- Point Route53 A-record to EC2 Elastic IP.
- Use Nginx + Certbot for TLS.

### Better scalable path

- Add ALB + ACM cert + target group to EC2.

## 6) Observability + cost guards

- CloudWatch logs for backend service and Nginx.
- Billing alerts with AWS Budgets.
- CloudWatch alarms for CPU, disk, and 5xx spikes.

## 7) Autoscaling upgrade path

When traffic grows:
1. Split upload API and workers.
2. Put job messages onto SQS.
3. Use EC2 Auto Scaling Group workers to process jobs.
4. Keep S3 as shared storage and Redis/RDS for durable job state.

## 8) Recommended production hardening

- Use PostgreSQL/RDS for `jobs` + `analysis_cache` tables instead of local SQLite
- Add WAF rate limits in front of ALB
- Add CloudFront for static frontend and frame preview caching
- Add cleanup cron/Lambda for stale data as your next iteration



