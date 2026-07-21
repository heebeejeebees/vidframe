# Google reCAPTCHA setup

This app supports backend-side CAPTCHA verification before allowing uploads.

## 1) Create reCAPTCHA keys

1. Go to Google reCAPTCHA admin console.
2. Register your site/domain.
3. Choose reCAPTCHA v2 checkbox (recommended for first rollout) or v3.
4. Save:
   - Site key (frontend)
   - Secret key (backend)

## 2) Backend config

Set these env vars on FastAPI host:

```bash
RECAPTCHA_ENABLED=true
RECAPTCHA_SECRET_KEY=your-secret-key
```

When enabled, `POST /api/jobs` requires `captcha_token`.

## 3) Frontend config

Set in `frontend/.env.local`:

```bash
VUE_APP_RECAPTCHA_SITE_KEY=your-site-key
```

Current implementation renders the reCAPTCHA v2 checkbox widget in `frontend/src/components/ProcessFile.vue`.
The frontend now performs a preflight call to `POST /api/captcha/verify` before upload, then sends the same token as `captcha_token` to `POST /api/jobs`.

## 4) Verify endpoint

Use `POST /api/captcha/verify` to test token validation quickly.

## 5) Ops notes

- Track failed captcha counts in logs.
- Rotate secret key if leaked.
- Keep domain allowlist strict in Google console.


