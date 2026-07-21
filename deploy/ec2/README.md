# EC2 deployment files

This directory contains baseline deployment artifacts for hosting frontend + backend on one EC2 instance.

## Files

- `deploy/ec2/systemd/vidframe-backend.service`
- `deploy/ec2/nginx/vidframe.conf`
- `deploy/ec2/env/backend.redis-db.env.example`
- `deploy/ec2/env/frontend.env.example`

## Assumed paths on EC2

- repo root: `/opt/vidframe`
- backend app: `/opt/vidframe/backend`
- backend venv: `/opt/vidframe/backend/.venv`
- frontend build output: `/opt/vidframe/frontend/dist`

Adjust paths in service and nginx files if your layout differs.

## Install systemd service

```bash
sudo cp /opt/vidframe/deploy/ec2/systemd/vidframe-backend.service /etc/systemd/system/vidframe-backend.service
sudo mkdir -p /etc/vidframe
sudo cp /opt/vidframe/deploy/ec2/env/backend.redis-db.env.example /etc/vidframe/backend.env
sudo systemctl daemon-reload
sudo systemctl enable vidframe-backend
sudo systemctl start vidframe-backend
sudo systemctl status vidframe-backend
```

## Install nginx site

```bash
sudo cp /opt/vidframe/deploy/ec2/nginx/vidframe.conf /etc/nginx/sites-available/vidframe.conf
sudo ln -s /etc/nginx/sites-available/vidframe.conf /etc/nginx/sites-enabled/vidframe.conf
sudo nginx -t
sudo systemctl reload nginx
```

If using Amazon Linux layout, place config under `/etc/nginx/conf.d/vidframe.conf` instead.

## Build frontend on server

```bash
cd /opt/vidframe/frontend
cp /opt/vidframe/deploy/ec2/env/frontend.env.example .env.production.local
npm ci
npm run build
```

## Backend runtime setup

```bash
cd /opt/vidframe/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Notes

- `client_max_body_size` in nginx should be >= backend max upload size.
- For TLS, place this behind ALB/ACM or use Certbot directly on nginx.
- `DATABASE_URL` and `REDIS_URL` are required for durable jobs and scalable dedup cache.



