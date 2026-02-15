const STORAGE_KEY = "vibe_sentinel_project_path";

const state = {
  artifacts: {},
};

const els = {
  projectPath: document.getElementById("artifactsProjectPath"),
  refreshBtn: document.getElementById("artifactsRefreshBtn"),
  shipBtn: document.getElementById("artifactsShipBtn"),
  list: document.getElementById("artifactsPageList"),
  previewTitle: document.getElementById("artifactsPagePreviewTitle"),
  preview: document.getElementById("artifactsPagePreview"),
  copyBtn: document.getElementById("artifactsCopyBtn"),
  timeline: document.getElementById("artifactsPageTimeline"),
  toast: document.getElementById("artifactsPageToast"),
};

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => {
    els.toast.classList.remove("show");
  }, 2200);
}

function timeline(message) {
  const item = document.createElement("li");
  item.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  els.timeline.prepend(item);
  while (els.timeline.children.length > 16) {
    els.timeline.removeChild(els.timeline.lastChild);
  }
}

function persistPath() {
  const value = els.projectPath.value.trim();
  if (value) {
    window.localStorage.setItem(STORAGE_KEY, value);
  }
}

function restorePath() {
  const value = window.localStorage.getItem(STORAGE_KEY);
  els.projectPath.value = value || ".";
}

async function postJSON(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function setPreview(title, content) {
  els.previewTitle.textContent = title;
  els.preview.textContent = content || "";
}

async function fetchArtifact(path) {
  const projectPath = els.projectPath.value.trim();
  if (!projectPath) {
    showToast("Project path is required.");
    return;
  }
  try {
    const payload = await postJSON("/api/artifact", {
      project_path: projectPath,
      artifact_path: path,
    });
    setPreview(payload.path, payload.content);
    timeline(`Loaded artifact preview: ${path}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    showToast(message);
    timeline(`Error: ${message}`);
  }
}

function renderArtifacts(artifacts) {
  state.artifacts = artifacts || {};
  els.list.innerHTML = "";
  const entries = Object.entries(state.artifacts);
  if (!entries.length) {
    const li = document.createElement("li");
    li.className = "artifact-item";
    li.textContent = "No artifacts available yet.";
    els.list.appendChild(li);
    return;
  }
  entries.forEach(([key, value]) => {
    const li = document.createElement("li");
    li.className = "artifact-item";
    li.textContent = `${key}: ${value}`;
    li.title = value;
    li.addEventListener("click", () => fetchArtifact(value));
    els.list.appendChild(li);
  });
}

async function runRefresh() {
  const projectPath = els.projectPath.value.trim();
  if (!projectPath) {
    showToast("Project path is required.");
    return;
  }

  persistPath();
  timeline("Refreshing artifacts via audit...");
  try {
    const payload = await postJSON("/api/audit", { project_path: projectPath });
    renderArtifacts(payload.artifacts || {});
    setPreview("Audit scorecard", JSON.stringify(payload.report?.scorecard || {}, null, 2));
    timeline("Artifact refresh complete.");
    showToast("Artifacts refreshed");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    timeline(`Error: ${message}`);
    showToast(message);
  }
}

async function runShipRefresh() {
  const projectPath = els.projectPath.value.trim();
  if (!projectPath) {
    showToast("Project path is required.");
    return;
  }

  persistPath();
  timeline("Running ship sequence...");
  try {
    const payload = await postJSON("/api/ship", {
      project_path: projectPath,
      apply_safe: true,
    });
    renderArtifacts(payload.artifacts || {});
    setPreview("Ship output", payload.agent_pack_markdown || payload.coach_markdown || "Ship complete.");
    timeline("Ship sequence complete. Artifacts updated.");
    showToast("Ship completed");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    timeline(`Error: ${message}`);
    showToast(message);
  }
}

function wireEvents() {
  els.projectPath.addEventListener("blur", persistPath);
  els.refreshBtn.addEventListener("click", runRefresh);
  els.shipBtn.addEventListener("click", runShipRefresh);
  els.copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(els.preview.textContent || "");
      showToast("Preview copied");
    } catch {
      showToast("Clipboard copy failed");
    }
  });
}

function init() {
  restorePath();
  wireEvents();
  timeline("Artifacts page ready.");
}

init();
