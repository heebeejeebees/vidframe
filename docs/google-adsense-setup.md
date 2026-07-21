# Google AdSense setup

Use this to monetize free usage while users wait for processing.

## 1) Create AdSense account

1. Sign up at AdSense.
2. Verify your site ownership/domain.
3. Wait for account approval.

## 2) Create ad units

Create at least:
- Responsive display ad for dashboard area
- Responsive display ad for processing page (progress wait area)

## 3) Add script to frontend

In your app shell (`frontend/src/App.vue`), inject AdSense script in `<head>` after approval:

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXX" crossorigin="anonymous"></script>
```

## 4) Render ad slot

Replace placeholders like `#ad-progress-slot` with AdSense `<ins class="adsbygoogle">` block and initialize via:

```js
(adsbygoogle = window.adsbygoogle || []).push({});
```

## 5) Policy and UX guardrails

- Do not place deceptive clickable ads near primary action buttons.
- Keep ad density moderate for retention.
- Show ad placeholder fallback when ad blockers are active.
- Track Core Web Vitals before/after ad insertion.

