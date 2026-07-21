const API_BASE_URL = (process.env.VUE_APP_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

function buildUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export async function verifyCaptchaPreflight(token) {
  const form = new FormData();
  form.append("token", token || "");

  const response = await fetch(buildUrl("/api/captcha/verify"), {
    method: "POST",
    body: form,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (err) {
    // keep payload as null and throw generic below
  }

  if (!response.ok) {
    const detail = payload && payload.detail ? payload.detail : `Captcha preflight failed (${response.status}).`;
    throw new Error(detail);
  }

  return payload;
}

export async function getBackendConfig() {
  const response = await fetch(buildUrl("/api/config"));
  if (!response.ok) {
    throw new Error(`Failed to load backend config (${response.status}).`);
  }
  return response.json();
}

export async function getJobStatus(jobId) {
  const response = await fetch(buildUrl(`/api/jobs/${jobId}`));
  if (!response.ok) {
    throw new Error(`Failed to fetch job status (${response.status}).`);
  }
  return response.json();
}

export async function getJobFrames(jobId) {
  const response = await fetch(buildUrl(`/api/jobs/${jobId}/frames`));
  if (!response.ok) {
    throw new Error(`Failed to fetch processed frames (${response.status}).`);
  }
  return response.json();
}

export function buildFramePreviewUrl(jobId, frameIndex) {
  return buildUrl(`/api/jobs/${jobId}/frame/${frameIndex}`);
}

export function buildFrameDownloadUrl(jobId, frameIndex) {
  return buildUrl(`/api/jobs/${jobId}/frame/${frameIndex}/download`);
}

export function uploadJob({ file, timeStart = "00:00", timeEnd = "00:00", captchaToken = "", onProgress }) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append("file", file);
    form.append("time_start", timeStart);
    form.append("time_end", timeEnd);
    form.append("captcha_token", captchaToken);

    xhr.open("POST", buildUrl("/api/jobs"));

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && typeof onProgress === "function") {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (err) {
          reject(new Error("Upload succeeded but response could not be parsed."));
        }
      } else {
        let detail = `Upload failed with status ${xhr.status}.`;
        try {
          const payload = JSON.parse(xhr.responseText);
          if (payload && payload.detail) {
            detail = payload.detail;
          }
        } catch (err) {
          // keep generic error
        }
        reject(new Error(detail));
      }
    };

    xhr.onerror = () => reject(new Error("Network error while uploading."));
    xhr.send(form);
  });
}

export { API_BASE_URL };



