const STORAGE_KEY = "vibe_sentinel_project_path";

const FLOW_STEPS = [
  "Audit baseline quality and surface top blockers.",
  "Run ship sequence to generate fixes and artifacts.",
  "Open coach output and execute plain-English actions.",
];

const els = {
  before: document.getElementById("storyBefore"),
  after: document.getElementById("storyAfter"),
  lift: document.getElementById("storyLift"),
  flowHint: document.getElementById("flowHint"),
  flowProgress: document.getElementById("flowProgress"),
  copyStarterCmdBtn: document.getElementById("copyStarterCmdBtn"),
  syncPathBtn: document.getElementById("syncPathBtn"),
  toast: document.getElementById("tutorialToast"),
  cards: Array.from(document.querySelectorAll(".tutorial-step-card")),
};

const state = {
  flowIndex: 0,
  flowTimer: null,
};

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => {
    els.toast.classList.remove("show");
  }, 2200);
}

function animateCounter(element, target, options = {}) {
  if (!element) {
    return;
  }
  const { forceSign = false } = options;
  const start = Number(element.dataset.value || 0);
  const duration = 520;
  const startTime = performance.now();

  function frame(now) {
    const t = Math.min((now - startTime) / duration, 1);
    const eased = 1 - (1 - t) ** 3;
    const value = start + (target - start) * eased;
    const text = forceSign ? `${value >= 0 ? "+" : ""}${value.toFixed(1)}` : value.toFixed(1);
    element.textContent = text;
    if (t < 1) {
      window.requestAnimationFrame(frame);
    } else {
      element.dataset.value = String(target);
      element.textContent = forceSign ? `${target >= 0 ? "+" : ""}${target.toFixed(1)}` : target.toFixed(1);
    }
  }

  window.requestAnimationFrame(frame);
}

function renderFlow() {
  const index = state.flowIndex % FLOW_STEPS.length;
  const progress = ((index + 1) / FLOW_STEPS.length) * 100;
  if (els.flowHint) {
    els.flowHint.textContent = FLOW_STEPS[index];
  }
  if (els.flowProgress) {
    els.flowProgress.style.width = `${progress}%`;
  }
  els.cards.forEach((card, cardIndex) => {
    card.classList.toggle("active", cardIndex === index);
  });
}

function startFlow() {
  renderFlow();
  state.flowTimer = window.setInterval(() => {
    state.flowIndex = (state.flowIndex + 1) % FLOW_STEPS.length;
    renderFlow();
  }, 2200);
}

function starterCommand() {
  const projectPath = window.localStorage.getItem(STORAGE_KEY) || "<your-project-path>";
  return `vibe-sentinel audit "${projectPath}" --output-dir .vibe-sentinel && vibe-sentinel ship "${projectPath}" --apply-safe`;
}

async function copyStarterCommand() {
  try {
    await navigator.clipboard.writeText(starterCommand());
    showToast("Starter command copied");
  } catch {
    showToast("Clipboard copy failed");
  }
}

function syncPath() {
  const path = window.localStorage.getItem(STORAGE_KEY);
  if (!path) {
    showToast("No project path found yet. Run Dashboard once first.");
    return;
  }
  showToast(`Using saved path: ${path}`);
}

function wireEvents() {
  if (els.copyStarterCmdBtn) {
    els.copyStarterCmdBtn.addEventListener("click", copyStarterCommand);
  }
  if (els.syncPathBtn) {
    els.syncPathBtn.addEventListener("click", syncPath);
  }
}

function init() {
  wireEvents();
  animateCounter(els.before, 31.5);
  animateCounter(els.after, 97.5);
  animateCounter(els.lift, 66.0, { forceSign: true });
  startFlow();
}

init();
