<template>
  <div id="process-wrapper">
    <h2>Uploading and Processing</h2>
    <p id="status">{{ statusText }}</p>

    <div class="progress-row">
      <label>Upload: {{ uploadProgress }}%</label>
      <progress :value="uploadProgress" max="100"></progress>
    </div>

    <div class="progress-row">
      <label>Processing: {{ processProgress }}%</label>
      <progress :value="processProgress" max="100"></progress>
    </div>

    <div class="progress-row">
      <label>Total: {{ totalProgress }}%</label>
      <progress :value="totalProgress" max="100"></progress>
    </div>

    <div class="captcha-box">
      <label>Human verification</label>
      <div v-if="captchaEnabled" ref="captchaContainer" id="recaptcha-container"></div>
      <p v-if="captchaEnabled" class="captcha-note">{{ captchaStatusText }}</p>
      <p v-else class="captcha-note">
        reCAPTCHA is not configured in frontend env (`VUE_APP_RECAPTCHA_SITE_KEY`).
      </p>
    </div>

    <div class="btn-row">
      <button class="btn" :disabled="isBusy || !canStartProcessing" @click="startProcessing">Start Processing</button>
      <button class="btn" :disabled="isBusy" @click="goHome">Cancel</button>
    </div>

    <p v-if="errorMessage" id="error">{{ errorMessage }}</p>

    <div id="ad-progress-slot">Ad space during processing</div>
  </div>
</template>

<script>
import { blobStore, framesStore } from '@/store';
import { getBackendConfig, getJobFrames, getJobStatus, uploadJob, verifyCaptchaPreflight } from '@/utils/api';

const RECAPTCHA_SCRIPT_SRC = 'https://www.google.com/recaptcha/api.js?render=explicit';
let recaptchaScriptPromise = null;

function loadRecaptchaScript() {
  if (window.grecaptcha && typeof window.grecaptcha.render === 'function') {
    return Promise.resolve(window.grecaptcha);
  }

  if (recaptchaScriptPromise) {
    return recaptchaScriptPromise;
  }

  recaptchaScriptPromise = new Promise((resolve, reject) => {
    const onLoaded = () => {
      if (window.grecaptcha && window.grecaptcha.ready) {
        window.grecaptcha.ready(() => resolve(window.grecaptcha));
      } else {
        reject(new Error('reCAPTCHA loaded but API was not ready.'));
      }
    };

    const existing = document.querySelector(`script[src="${RECAPTCHA_SCRIPT_SRC}"]`);
    if (existing) {
      existing.addEventListener('load', onLoaded, { once: true });
      existing.addEventListener('error', () => reject(new Error('Failed to load reCAPTCHA script.')), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = RECAPTCHA_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = onLoaded;
    script.onerror = () => reject(new Error('Failed to load reCAPTCHA script.'));
    document.head.appendChild(script);
  });

  return recaptchaScriptPromise;
}

export default {
  name: 'Process',
  data() {
    return {
      uploadProgress: 0,
      processProgress: 0,
      statusText: 'Ready to process your file on the backend.',
      captchaToken: '',
      captchaWidgetId: null,
      captchaReady: false,
      captchaStatusText: 'Loading CAPTCHA...',
      siteKey: process.env.VUE_APP_RECAPTCHA_SITE_KEY || '',
      backendRecaptchaEnabled: true,
      errorMessage: '',
      jobId: null,
      pollIntervalId: null,
      isBusy: false,
    };
  },
  computed: {
    captchaEnabled() {
      return Boolean(this.siteKey) && this.backendRecaptchaEnabled;
    },
    canStartProcessing() {
      return !this.captchaEnabled || Boolean(this.captchaToken);
    },
    totalProgress() {
      // Weight upload and backend compute equally for a simple user-facing indicator.
      return Math.round((this.uploadProgress + this.processProgress) / 2);
    },
  },
  mounted() {
    const file = blobStore.getters.getBlob();
    if (!file) {
      this.goHome();
      return;
    }

    this.loadBackendConfig().finally(() => {
      if (this.captchaEnabled) {
        this.initRecaptcha();
      } else {
        this.captchaStatusText = 'CAPTCHA is not required by backend.';
      }
    });
  },
  unmounted() {
    if (this.pollIntervalId) {
      clearInterval(this.pollIntervalId);
    }
    this.resetRecaptcha();
  },
  methods: {
    async loadBackendConfig() {
      try {
        const cfg = await getBackendConfig();
        this.backendRecaptchaEnabled = Boolean(cfg.recaptcha_enabled);
      } catch (err) {
        // Fallback to requiring captcha when backend config cannot be loaded.
        this.backendRecaptchaEnabled = true;
      }
    },
    async initRecaptcha() {
      this.captchaStatusText = 'Loading CAPTCHA...';

      try {
        const grecaptcha = await loadRecaptchaScript();
        if (!this.$refs.captchaContainer) {
          return;
        }

        this.captchaWidgetId = grecaptcha.render(this.$refs.captchaContainer, {
          sitekey: this.siteKey,
          callback: (token) => {
            this.captchaToken = token;
            this.captchaReady = true;
            this.captchaStatusText = 'Verification complete.';
          },
          'expired-callback': () => {
            this.captchaToken = '';
            this.captchaStatusText = 'Verification expired. Please verify again.';
          },
          'error-callback': () => {
            this.captchaToken = '';
            this.captchaStatusText = 'CAPTCHA error. Please retry.';
          },
        });

        this.captchaReady = true;
        this.captchaStatusText = 'Please complete CAPTCHA before processing.';
      } catch (err) {
        this.captchaToken = '';
        this.captchaReady = false;
        this.captchaStatusText = 'Unable to load CAPTCHA widget.';
        this.errorMessage = err.message || 'Failed to initialize reCAPTCHA.';
      }
    },
    resetRecaptcha() {
      if (!this.captchaEnabled) {
        return;
      }
      if (window.grecaptcha && this.captchaWidgetId !== null) {
        window.grecaptcha.reset(this.captchaWidgetId);
      }
      this.captchaToken = '';
    },
    async startProcessing() {
      const file = blobStore.getters.getBlob();
      if (!file) {
        this.goHome();
        return;
      }

      if (this.captchaEnabled && !this.captchaToken) {
        this.errorMessage = 'Please complete CAPTCHA before starting upload.';
        return;
      }

      this.errorMessage = '';
      this.isBusy = true;
      this.uploadProgress = 0;
      this.processProgress = 0;
      this.statusText = 'Validating CAPTCHA...';

      try {
        if (this.captchaEnabled) {
          await verifyCaptchaPreflight(this.captchaToken);
          this.captchaStatusText = 'Verification accepted by backend.';
        }

        this.statusText = 'Uploading to backend...';
        const created = await uploadJob({
          file,
          captchaToken: this.captchaToken,
          onProgress: (pct) => {
            this.uploadProgress = pct;
          },
        });

        this.jobId = created.job_id;
        framesStore.mutations.setJobId(created.job_id);

        if (created.status === 'done') {
          this.uploadProgress = 100;
          this.processProgress = 100;
          await this.fetchFramesAndGoResult();
          return;
        }

        this.statusText = 'Upload complete. Processing video...';
        this.uploadProgress = 100;
        this.pollUntilDone();
      } catch (err) {
        this.errorMessage = err.message || 'Failed to start processing.';
        this.statusText = 'Unable to process this file.';
        this.isBusy = false;
        this.resetRecaptcha();
      }
    },
    pollUntilDone() {
      if (!this.jobId) {
        this.errorMessage = 'Missing job id.';
        this.isBusy = false;
        return;
      }

      this.pollIntervalId = setInterval(async () => {
        try {
          const status = await getJobStatus(this.jobId);
          this.processProgress = status.progress_pct || 0;

          if (status.status === 'failed') {
            clearInterval(this.pollIntervalId);
            this.pollIntervalId = null;
            this.errorMessage = status.error || 'Processing failed.';
            this.statusText = 'Processing failed.';
            this.isBusy = false;
            return;
          }

          if (status.status === 'done') {
            clearInterval(this.pollIntervalId);
            this.pollIntervalId = null;
            this.processProgress = 100;
            await this.fetchFramesAndGoResult();
          }
        } catch (err) {
          clearInterval(this.pollIntervalId);
          this.pollIntervalId = null;
          this.errorMessage = err.message || 'Polling failed.';
          this.isBusy = false;
        }
      }, 1000);
    },
    async fetchFramesAndGoResult() {
      try {
        this.statusText = 'Preparing timeline data...';
        const payload = await getJobFrames(this.jobId);
        const apiFrames = payload.analysis?.frames || [];

        const mappedFrames = apiFrames.map((frame) => ({
          index: frame.index,
          data: {
            laplacian_variance: frame.laplacian_variance,
          },
          timestamp: frame.timestamp,
          timestamp_microseconds: frame.index,
        }));

        framesStore.mutations.setFrames(mappedFrames);
        this.isBusy = false;
        this.$router.replace({ name: 'Result' });
      } catch (err) {
        this.errorMessage = err.message || 'Failed to load processed frames.';
        this.statusText = 'Unable to load analysis.';
        this.isBusy = false;
      }
    },
    goHome() {
      framesStore.actions.clearFrames();
      this.$router.replace({ name: 'Home' });
    },
  },
};
</script>

<style scoped>
#process-wrapper {
  width: min(820px, 95vw);
  margin: 4vh auto;
  color: var(--font-p-color);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

h2 {
  color: var(--font-h-color);
}

#status {
  margin: 0;
}

.progress-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

progress {
  width: 100%;
  height: 18px;
}

.captcha-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

#recaptcha-container {
  min-height: 78px;
}

.captcha-note {
  margin: 0;
  font-size: 0.9rem;
  color: var(--font-p-color);
}

.btn-row {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: var(--primary-color);
  color: var(--background-color);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

#error {
  color: #ff8e8e;
}

#ad-progress-slot {
  margin-top: 10px;
  border: 1px dashed var(--secondary-color);
  padding: 12px;
  border-radius: 6px;
  color: var(--font-p-color);
}
</style>