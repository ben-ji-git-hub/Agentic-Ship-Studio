const PATH_STORAGE_KEY = "vibe_sentinel_project_path";
const KEY_STORAGE_KEY = "vibe_sentinel_openclaw_key";

const els = {
  projectPath: document.getElementById("openclawProjectPath"),
  apiKey: document.getElementById("openclawApiKey"),
  action: document.getElementById("openclawAction"),
  applySafe: document.getElementById("openclawApplySafe"),
  probeBtn: document.getElementById("openclawProbeBtn"),
  runBtn: document.getElementById("openclawRunBtn"),
  copyCurlBtn: document.getElementById("openclawCopyCurlBtn"),
  copyRequestBtn: document.getElementById("openclawCopyRequestBtn"),
  statusText: document.getElementById("openclawStatusText"),
  statusPreview: document.getElementById("openclawStatusPreview"),
  runPreview: document.getElementById("openclawRunPreview"),
  timeline: document.getElementById("openclawTimeline"),
  badge: document.getElementById("openclawBridgeBadge"),
  toast: document.getElementById("openclawToast"),
};

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => {
    els.toast.classList.remove("show");
  }, 2200);
}

function addTimeline(message) {
  const item = document.createElement("li");
  item.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  els.timeline.prepend(item);
  while (els.timeline.children.length > 16) {
    els.timeline.removeChild(els.timeline.lastChild);
  }
}

function persistFields() {
  const pathValue = els.projectPath.value.trim();
  if (pathValue) {
    window.localStorage.setItem(PATH_STORAGE_KEY, pathValue);
  }
  const keyValue = els.apiKey.value.trim();
  if (keyValue) {
    window.localStorage.setItem(KEY_STORAGE_KEY, keyValue);
  } else {
    window.localStorage.removeItem(KEY_STORAGE_KEY);
  }
}

function restoreFields() {
  els.projectPath.value = window.localStorage.getItem(PATH_STORAGE_KEY) || ".";
  els.apiKey.value = window.localStorage.getItem(KEY_STORAGE_KEY) || "";
}

function openclawHeaders() {
  const headers = { "Content-Type": "application/json" };
  const key = els.apiKey.value.trim();
  if (key) {
    headers["X-OpenClaw-Key"] = key;
  }
  return headers;
}

function currentPayload() {
  return {
    project_path: els.projectPath.value.trim(),
    action: els.action.value,
    apply_safe: Boolean(els.applySafe.checked),
  };
}

async function parseJSON(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function probeBridge() {
  persistFields();
  addTimeline("Probing OpenClaw bridge...");
  try {
    const response = await fetch("/api/openclaw/status", {
      method: "GET",
      headers: openclawHeaders(),
    });
    const payload = await parseJSON(response);
    els.statusText.textContent = "Bridge is available and ready.";
    els.statusPreview.textContent = JSON.stringify(payload, null, 2);
    els.badge.className = "hero-badge strong";
    els.badge.textContent = "Bridge ready";
    addTimeline("Bridge probe succeeded.");
    showToast("Bridge is up");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    els.statusText.textContent = message;
    els.statusPreview.textContent = message;
    els.badge.className = "hero-badge critical";
    els.badge.textContent = "Bridge blocked";
    addTimeline(`Bridge probe failed: ${message}`);
    showToast(message);
  }
}

async function runBridgeAction() {
  const payload = currentPayload();
  if (!payload.project_path) {
    showToast("Project path is required.");
    return;
  }

  persistFields();
  addTimeline(`Running OpenClaw action: ${payload.action}`);
  try {
    const response = await fetch("/api/openclaw/execute", {
      method: "POST",
      headers: openclawHeaders(),
      body: JSON.stringify(payload),
    });
    const result = await parseJSON(response);
    els.runPreview.textContent = JSON.stringify(result, null, 2);
    addTimeline(`OpenClaw action complete: ${payload.action}`);
    showToast("Action completed");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    els.runPreview.textContent = message;
    addTimeline(`Action failed: ${message}`);
    showToast(message);
  }
}

function curlCommand() {
  const payload = currentPayload();
  const key = els.apiKey.value.trim();
  const keyHeader = key ? ` -H "X-OpenClaw-Key: ${key}"` : "";
  const base = window.location.origin;
  return (
    `curl -X POST "${base}/api/openclaw/execute"` +
    ` -H "Content-Type: application/json"${keyHeader}` +
    ` -d '${JSON.stringify(payload)}'`
  );
}

async function copyCurl() {
  try {
    await navigator.clipboard.writeText(curlCommand());
    showToast("cURL copied");
  } catch {
    showToast("Clipboard copy failed");
  }
}

async function copyRequestJSON() {
  try {
    await navigator.clipboard.writeText(JSON.stringify(currentPayload(), null, 2));
    showToast("Request JSON copied");
  } catch {
    showToast("Clipboard copy failed");
  }
}

function wireEvents() {
  els.projectPath.addEventListener("blur", persistFields);
  els.apiKey.addEventListener("blur", persistFields);
  els.probeBtn.addEventListener("click", probeBridge);
  els.runBtn.addEventListener("click", runBridgeAction);
  els.copyCurlBtn.addEventListener("click", copyCurl);
  els.copyRequestBtn.addEventListener("click", copyRequestJSON);
}

function init() {
  restoreFields();
  wireEvents();
  addTimeline("OpenClaw page ready.");
}

init();
