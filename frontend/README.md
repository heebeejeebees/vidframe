# VideoFra.me frontend

Vue app for upload UI, processing progress, timeline chart, frame preview, and frame download.

## Implemented

- Upload videos from browser and send to FastAPI backend
- Show upload + backend processing progress bars
- Poll backend job endpoint and render laplacian timeline
- Preview/download selected frame through backend API
- reCAPTCHA v2 checkbox widget with backend preflight verification before upload
- Processing-page ad placeholder slot

## Environment variables

Create `frontend/.env.local`:

```bash
VUE_APP_API_BASE_URL=http://127.0.0.1:8000
VUE_APP_RECAPTCHA_SITE_KEY=
```

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
