const state = {
  loading: false,
  report: null,
  insights: null,
  artifacts: {},
  tasks: [],
  history: [],
  simSelections: new Set(),
  simItems: [],
  lastScore: null,
  tourTimer: null,
  tourIndex: -1,
  tourRunning: false,
  uiShowAdvanced: false,
  lastOpenedArtifact: "",
  tutorialStarted: false,
  tutorialTourSeen: false,
};

const STORAGE_KEY = "vibe_sentinel_project_path";

const MILESTONES = [
  { threshold: 60, label: "Bronze Ready", note: "Baseline reliability unlocked" },
  { threshold: 75, label: "Silver Ship", note: "Judge-facing confidence zone" },
  { threshold: 90, label: "Gold Launch", note: "Competition-grade quality bar" },
];

const TOUR_FLOW = [
  { label: "Score Story", target: "scorePanel", note: "Explain overall score and category blend." },
  { label: "Fix Simulator", target: "simulatorPanel", note: "Preview score lift from top fixes." },
  { label: "Findings", target: "findingsPanel", note: "Show concrete gaps and recommendations." },
  { label: "Agent Queue", target: "tasksPanel", note: "Show autonomous task handoff." },
  { label: "Artifacts", target: "previewPanel", note: "Open generated markdown and prompts." },
  { label: "Timeline", target: "timelinePanel", note: "Close with repeatable execution history." },
];

const TUTORIAL_STEPS = [
  {
    id: "path",
    label: "Set project path",
    hint: "Paste your project path in the top input.",
    target: "projectPath",
  },
  {
    id: "audit",
    label: "Run baseline audit",
    hint: "Click 'Run Audit' to generate a baseline score and findings.",
    target: "auditBtn",
  },
  {
    id: "review",
    label: "Review findings",
    hint: "Read Top Actions and Open Findings to understand what blocks shipping.",
    target: "findingsPanel",
  },
  {
    id: "ship",
    label: "Run ship sequence",
    hint: "Click 'Launch Ship Sequence' for the full improvement loop.",
    target: "shipBtn",
  },
  {
    id: "coach",
    label: "Open beginner coach output",
    hint: "Open the coach artifact to get plain-English fix cards.",
    target: "artifactList",
  },
  {
    id: "tour",
    label: "Run demo tour",
    hint: "Start Demo Tour for an automatic walkthrough flow.",
    target: "startTourBtn",
  },
];

const els = {
  projectPath: document.getElementById("projectPath"),
  applySafeToggle: document.getElementById("applySafeToggle"),
  auditBtn: document.getElementById("auditBtn"),
  packBtn: document.getElementById("packBtn"),
  coachBtn: document.getElementById("coachBtn"),
  roadmapBtn: document.getElementById("roadmapBtn"),
  shipBtn: document.getElementById("shipBtn"),
  tutorialStartBtn: document.getElementById("tutorialStartBtn"),
  tutorialNextBtn: document.getElementById("tutorialNextBtn"),
  toggleAdvancedBtn: document.getElementById("toggleAdvancedBtn"),
  advancedActions: document.getElementById("advancedActions"),
  clearHistoryBtn: document.getElementById("clearHistoryBtn"),
  scoreBandBadge: document.getElementById("scoreBandBadge"),
  overallDial: document.getElementById("overallDial"),
  overallScore: document.getElementById("overallScore"),
  deltaPill: document.getElementById("deltaPill"),
  passRate: document.getElementById("passRate"),
  usefulnessValue: document.getElementById("usefulnessValue"),
  impactValue: document.getElementById("impactValue"),
  executionValue: document.getElementById("executionValue"),
  innovationValue: document.getElementById("innovationValue"),
  usefulnessBar: document.getElementById("usefulnessBar"),
  impactBar: document.getElementById("impactBar"),
  executionBar: document.getElementById("executionBar"),
  innovationBar: document.getElementById("innovationBar"),
  passCount: document.getElementById("passCount"),
  warnCount: document.getElementById("warnCount"),
  failCount: document.getElementById("failCount"),
  highCount: document.getElementById("highCount"),
  mediumCount: document.getElementById("mediumCount"),
  lowCount: document.getElementById("lowCount"),
  topActions: document.getElementById("topActions"),
  historyList: document.getElementById("historyList"),
  findingsList: document.getElementById("findingsList"),
  taskRows: document.getElementById("taskRows"),
  artifactList: document.getElementById("artifactList"),
  previewTitle: document.getElementById("previewTitle"),
  previewContent: document.getElementById("previewContent"),
  copyPreviewBtn: document.getElementById("copyPreviewBtn"),
  timelineList: document.getElementById("timelineList"),
  toast: document.getElementById("toast"),
  simCurrentScore: document.getElementById("simCurrentScore"),
  simProjectedScore: document.getElementById("simProjectedScore"),
  simLift: document.getElementById("simLift"),
  simProgressBar: document.getElementById("simProgressBar"),
  simChecklist: document.getElementById("simChecklist"),
  milestoneList: document.getElementById("milestoneList"),
  milestoneStatus: document.getElementById("milestoneStatus"),
  milestonePanel: document.getElementById("milestonePanel"),
  startTourBtn: document.getElementById("startTourBtn"),
  stopTourBtn: document.getElementById("stopTourBtn"),
  tourSteps: document.getElementById("tourSteps"),
  tourProgressBar: document.getElementById("tourProgressBar"),
  celebrationLayer: document.getElementById("celebrationLayer"),
  tutorialPanel: document.getElementById("tutorialPanel"),
  tutorialSteps: document.getElementById("tutorialSteps"),
  tutorialHint: document.getElementById("tutorialHint"),
  tutorialProgressBar: document.getElementById("tutorialProgressBar"),
  tutorialStatusBadge: document.getElementById("tutorialStatusBadge"),
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
  els.timelineList.prepend(item);
  while (els.timelineList.children.length > 16) {
    els.timelineList.removeChild(els.timelineList.lastChild);
  }
}

function setLoading(value) {
  state.loading = value;
  [
    els.auditBtn,
    els.packBtn,
    els.coachBtn,
    els.roadmapBtn,
    els.shipBtn,
    els.startTourBtn,
    els.tutorialStartBtn,
    els.tutorialNextBtn,
    els.toggleAdvancedBtn,
  ].forEach((button) => {
    if (button) {
      button.disabled = value;
    }
  });
}

function clampScore(value) {
  return Math.max(0, Math.min(100, Number(value || 0)));
}

function animateNumber(element, target, options = {}) {
  const { decimals = 1, suffix = "", forceSign = false } = options;
  const end = Number.isFinite(target) ? Number(target) : 0;
  const start = Number(element.dataset.numericValue || 0);
  const duration = 420;
  const startTime = performance.now();

  function format(value) {
    const base = value.toFixed(decimals);
    if (forceSign) {
      return `${value >= 0 ? "+" : ""}${base}${suffix}`;
    }
    return `${base}${suffix}`;
  }

  function frame(now) {
    const t = Math.min((now - startTime) / duration, 1);
    const eased = 1 - (1 - t) ** 3;
    const value = start + (end - start) * eased;
    element.textContent = format(value);
    if (t < 1) {
      window.requestAnimationFrame(frame);
    } else {
      element.dataset.numericValue = String(end);
      element.textContent = format(end);
    }
  }

  window.requestAnimationFrame(frame);
}

function setScoreBadge(scoreBand) {
  const labelMap = {
    excellent: "Excellent",
    strong: "Strong",
    "needs-work": "Needs Work",
    critical: "Critical",
  };
  els.scoreBandBadge.className = "hero-badge";
  if (scoreBand) {
    els.scoreBandBadge.classList.add(scoreBand);
  }
  els.scoreBandBadge.textContent = labelMap[scoreBand] || "Awaiting run";
}

function updateScoreCard(report, insights, improvement) {
  if (!report || !report.scorecard) {
    return;
  }

  const score = report.scorecard;
  const overall = clampScore(score.overall);
  els.overallDial.style.setProperty("--score", overall);
  animateNumber(els.overallScore, overall);

  const categories = [
    ["usefulness", els.usefulnessValue, els.usefulnessBar],
    ["impact", els.impactValue, els.impactBar],
    ["execution", els.executionValue, els.executionBar],
    ["innovation", els.innovationValue, els.innovationBar],
  ];

  categories.forEach(([key, valueEl, barEl]) => {
    const value = clampScore(score[key]);
    animateNumber(valueEl, value);
    barEl.style.width = `${value}%`;
  });

  if (typeof improvement === "number") {
    els.deltaPill.textContent = `Ship delta: ${improvement >= 0 ? "+" : ""}${improvement.toFixed(1)} pts`;
  } else {
    els.deltaPill.textContent = "Run Ship Sequence for full before/after delta";
  }

  const passRate = Number(insights?.pass_rate ?? 0);
  els.passRate.textContent = `Pass rate: ${passRate.toFixed(1)}%`;
  setScoreBadge(insights?.score_band || "");
}

function renderBreakdown(insights) {
  if (!insights) {
    return;
  }
  const statuses = insights.status_counts || {};
  const severities = insights.severity_counts || {};
  els.passCount.textContent = statuses.pass ?? 0;
  els.warnCount.textContent = statuses.warn ?? 0;
  els.failCount.textContent = statuses.fail ?? 0;
  els.highCount.textContent = severities.high ?? 0;
  els.mediumCount.textContent = severities.medium ?? 0;
  els.lowCount.textContent = severities.low ?? 0;

  els.topActions.innerHTML = "";
  const actions = insights.top_actions || [];
  if (!actions.length) {
    const li = document.createElement("li");
    li.textContent = "No immediate fixes. Maintain current quality baseline.";
    els.topActions.appendChild(li);
    return;
  }

  actions.forEach((action) => {
    const li = document.createElement("li");
    li.textContent = action;
    els.topActions.appendChild(li);
  });
}

function findingSortWeight(item) {
  const severityWeight = { high: 0, medium: 1, low: 2 };
  const statusWeight = { fail: 0, warn: 1, pass: 2 };
  return [statusWeight[item.status] ?? 2, severityWeight[item.severity] ?? 2];
}

function renderFindings(report) {
  els.findingsList.innerHTML = "";
  if (!report || !Array.isArray(report.checks)) {
    return;
  }

  const findings = report.checks
    .filter((item) => item.status !== "pass")
    .sort((a, b) => {
      const wa = findingSortWeight(a);
      const wb = findingSortWeight(b);
      if (wa[0] !== wb[0]) {
        return wa[0] - wb[0];
      }
      return wa[1] - wb[1];
    });

  if (!findings.length) {
    const empty = document.createElement("p");
    empty.className = "detail";
    empty.textContent = "No open findings.";
    els.findingsList.appendChild(empty);
    return;
  }

  findings.forEach((finding) => {
    const node = document.createElement("article");
    node.className = "finding";
    node.innerHTML = `
      <div class="finding-head">
        <span class="sev ${finding.severity}">${String(finding.severity || "low").toUpperCase()}</span>
        <strong>${finding.title}</strong>
      </div>
      <p>${finding.detail}</p>
      <p>Fix: ${finding.recommendation}</p>
    `;
    els.findingsList.appendChild(node);
  });
}

function renderTaskQueue(tasks) {
  els.taskRows.innerHTML = "";
  if (!Array.isArray(tasks) || tasks.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="4">No agent tasks queued.</td>`;
    els.taskRows.appendChild(row);
    return;
  }

  tasks.forEach((task) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${task.task_id}</td>
      <td>${String(task.severity || "").toUpperCase()}</td>
      <td>${task.title}</td>
      <td>${task.estimated_minutes}m</td>
    `;
    els.taskRows.appendChild(row);
  });
}

function setPreview(title, content) {
  els.previewTitle.textContent = title;
  els.previewContent.textContent = content || "";
}

async function fetchArtifact(artifactPath) {
  const projectPath = els.projectPath.value.trim();
  if (!projectPath) {
    showToast("Set a project path first.");
    return;
  }

  try {
    const payload = await postJSON("/api/artifact", {
      project_path: projectPath,
      artifact_path: artifactPath,
    });
    state.lastOpenedArtifact = String(payload.path || artifactPath);
    setPreview(payload.path, payload.content);
    renderTutorial();
    showToast("Loaded artifact preview");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    showToast(message);
  }
}

function renderArtifacts(artifacts) {
  state.artifacts = artifacts || {};
  els.artifactList.innerHTML = "";

  const entries = Object.entries(state.artifacts);
  if (!entries.length) {
    const item = document.createElement("li");
    item.textContent = "No artifacts yet.";
    item.className = "artifact-item";
    els.artifactList.appendChild(item);
    return;
  }

  entries.forEach(([key, value]) => {
    const item = document.createElement("li");
    item.className = "artifact-item";
    item.textContent = `${key}: ${value}`;
    item.title = value;
    item.addEventListener("click", () => fetchArtifact(value));
    els.artifactList.appendChild(item);
  });
}

function updateHistory(action, score, delta) {
  const entry = {
    action,
    score: Number(score || 0),
    delta: typeof delta === "number" ? delta : null,
    at: new Date().toLocaleTimeString(),
  };
  state.history.unshift(entry);
  state.history = state.history.slice(0, 10);
  renderHistory();
}

function renderHistory() {
  els.historyList.innerHTML = "";
  if (!state.history.length) {
    const item = document.createElement("li");
    item.textContent = "No runs yet.";
    els.historyList.appendChild(item);
    return;
  }

  state.history.forEach((entry) => {
    const item = document.createElement("li");
    const width = clampScore(entry.score);
    const deltaText = entry.delta === null ? "" : ` (${entry.delta >= 0 ? "+" : ""}${entry.delta.toFixed(1)})`;
    item.innerHTML = `
      <div class="history-row">
        <span>${entry.at} • ${entry.action}</span>
        <span>${entry.score.toFixed(1)}${deltaText}</span>
      </div>
      <div class="history-bar"><i style="width:${width}%"></i></div>
    `;
    els.historyList.appendChild(item);
  });
}

function setAdvancedActionsVisible(show) {
  state.uiShowAdvanced = show;
  if (!els.advancedActions) {
    return;
  }
  els.advancedActions.classList.toggle("is-hidden", !show);
  els.toggleAdvancedBtn.textContent = show ? "Hide Advanced Actions" : "Show Advanced Actions";
}

function focusTutorialTarget(targetId) {
  const target = document.getElementById(targetId);
  if (!target) {
    return;
  }
  target.classList.add("tour-focus");
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  window.setTimeout(() => target.classList.remove("tour-focus"), 850);
  if (target instanceof HTMLInputElement || target instanceof HTMLButtonElement) {
    target.focus();
  }
}

function tutorialCompletionMap() {
  const hasPath = Boolean(els.projectPath.value.trim());
  const hasAudit = state.history.some((entry) => entry.action === "audit");
  const hasReport = Boolean(state.report);
  const hasShip = state.history.some((entry) => entry.action === "ship");
  const hasCoachArtifactOpen =
    state.lastOpenedArtifact.endsWith("coach.md") || String(els.previewTitle.textContent).toLowerCase().includes("coach");
  const hasTour = state.tutorialTourSeen;

  return {
    path: hasPath,
    audit: hasAudit,
    review: hasReport,
    ship: hasShip,
    coach: hasCoachArtifactOpen,
    tour: hasTour,
  };
}

function tutorialProgressStats() {
  const completion = tutorialCompletionMap();
  const done = TUTORIAL_STEPS.filter((step) => completion[step.id]).length;
  const total = TUTORIAL_STEPS.length;
  const firstIncomplete = TUTORIAL_STEPS.find((step) => !completion[step.id]) || null;
  return { completion, done, total, firstIncomplete };
}

function renderTutorial() {
  const { completion, done, total, firstIncomplete } = tutorialProgressStats();
  const percent = total === 0 ? 0 : (done / total) * 100;
  els.tutorialProgressBar.style.width = `${percent}%`;
  els.tutorialSteps.innerHTML = "";

  TUTORIAL_STEPS.forEach((step) => {
    const li = document.createElement("li");
    li.className = completion[step.id] ? "done" : "";
    li.innerHTML = `<strong>${step.label}</strong><span>${completion[step.id] ? "Done" : "Pending"}</span>`;
    els.tutorialSteps.appendChild(li);
  });

  if (!state.tutorialStarted) {
    els.tutorialStatusBadge.className = "hero-badge";
    els.tutorialStatusBadge.textContent = "Not started";
    return;
  }

  if (done === total) {
    els.tutorialStatusBadge.className = "hero-badge excellent";
    els.tutorialStatusBadge.textContent = "Complete";
    els.tutorialHint.textContent = "Great. You completed the beginner flow and can now use advanced actions as needed.";
    return;
  }

  els.tutorialStatusBadge.className = "hero-badge strong";
  els.tutorialStatusBadge.textContent = `${done}/${total} steps`;
  els.tutorialHint.textContent = firstIncomplete ? firstIncomplete.hint : "Continue to the next step.";
}

async function runTutorialNextStep() {
  state.tutorialStarted = true;
  renderTutorial();
  const { firstIncomplete } = tutorialProgressStats();
  if (!firstIncomplete) {
    showToast("Tutorial already complete.");
    return;
  }

  focusTutorialTarget(firstIncomplete.target);

  if (firstIncomplete.id === "audit") {
    await runAction("audit");
    return;
  }
  if (firstIncomplete.id === "ship") {
    await runAction("ship");
    return;
  }
  if (firstIncomplete.id === "coach") {
    const coachPath = Object.entries(state.artifacts).find(([key]) => key === "coach_markdown")?.[1];
    if (coachPath) {
      await fetchArtifact(coachPath);
      return;
    }
    await runAction("coach");
    return;
  }
  if (firstIncomplete.id === "tour") {
    startTour();
    return;
  }

  showToast(firstIncomplete.hint);
}

function persistPath() {
  const value = els.projectPath.value.trim();
  if (value) {
    window.localStorage.setItem(STORAGE_KEY, value);
  }
  renderTutorial();
}

function restorePath() {
  const fromStorage = window.localStorage.getItem(STORAGE_KEY);
  els.projectPath.value = fromStorage || ".";
}

function liftForFinding(status, severity) {
  const matrix = {
    fail: { high: 8, medium: 5, low: 3 },
    warn: { high: 4, medium: 3, low: 2 },
  };
  return matrix[status]?.[severity] ?? 2;
}

function simulatorItemsFromReport(report) {
  if (!report || !Array.isArray(report.checks)) {
    return [];
  }

  return report.checks
    .filter((item) => item.status !== "pass")
    .sort((a, b) => {
      const wa = findingSortWeight(a);
      const wb = findingSortWeight(b);
      if (wa[0] !== wb[0]) {
        return wa[0] - wb[0];
      }
      return wa[1] - wb[1];
    })
    .slice(0, 7)
    .map((item, index) => ({
      id: `${item.check_id || "check"}-${index}`,
      title: item.title,
      status: item.status,
      severity: item.severity,
      lift: liftForFinding(item.status, item.severity),
    }));
}

function renderSimulator(report) {
  const items = simulatorItemsFromReport(report);
  state.simItems = items;

  const currentIds = new Set(items.map((item) => item.id));
  state.simSelections = new Set([...state.simSelections].filter((id) => currentIds.has(id)));

  els.simChecklist.innerHTML = "";
  if (!items.length) {
    const row = document.createElement("li");
    row.className = "sim-item";
    row.textContent = "No open findings. Simulator is clean.";
    els.simChecklist.appendChild(row);
    updateSimulatorMetrics();
    return;
  }

  items.forEach((item) => {
    const row = document.createElement("li");
    row.className = "sim-item";
    row.innerHTML = `
      <label>
        <input type="checkbox" data-sim-id="${item.id}" />
        <span>${item.title}</span>
      </label>
      <div class="sim-tags">
        <span class="tag ${item.severity}">${String(item.severity).toUpperCase()}</span>
        <span class="tag neutral">${String(item.status).toUpperCase()}</span>
        <span class="tag lift">+${item.lift.toFixed(1)}</span>
      </div>
    `;
    const checkbox = row.querySelector("input");
    checkbox.checked = state.simSelections.has(item.id);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        state.simSelections.add(item.id);
      } else {
        state.simSelections.delete(item.id);
      }
      updateSimulatorMetrics();
    });
    els.simChecklist.appendChild(row);
  });

  updateSimulatorMetrics();
}

function updateSimulatorMetrics() {
  const current = clampScore(state.report?.scorecard?.overall || 0);
  let lift = 0;
  state.simItems.forEach((item) => {
    if (state.simSelections.has(item.id)) {
      lift += item.lift;
    }
  });

  const projected = clampScore(current + lift);
  animateNumber(els.simCurrentScore, current);
  animateNumber(els.simProjectedScore, projected);
  animateNumber(els.simLift, lift, { forceSign: true });
  els.simProgressBar.style.width = `${projected}%`;
}

function renderMilestones(score) {
  els.milestoneList.innerHTML = "";
  if (!Number.isFinite(score)) {
    els.milestoneStatus.textContent = "Run an action to populate milestones.";
    return;
  }

  MILESTONES.forEach((milestone) => {
    const li = document.createElement("li");
    li.className = "milestone";
    if (score >= milestone.threshold) {
      li.classList.add("reached");
    }
    li.innerHTML = `
      <span class="milestone-dot"></span>
      <div>
        <strong>${milestone.label}</strong>
        <p>${milestone.threshold}+ points • ${milestone.note}</p>
      </div>
    `;
    els.milestoneList.appendChild(li);
  });

  const reached = MILESTONES.filter((milestone) => score >= milestone.threshold);
  if (!reached.length) {
    els.milestoneStatus.textContent = "No milestone unlocked yet. Focus high-impact fixes first.";
    return;
  }

  const latest = reached[reached.length - 1];
  els.milestoneStatus.textContent = `Latest milestone: ${latest.label} (${score.toFixed(1)} points).`;
  const active = els.milestoneList.children[reached.length - 1];
  if (active) {
    active.classList.add("current");
  }
}

function triggerCelebration(label) {
  const colors = ["#30d8b2", "#53c6ff", "#ffb84c", "#ff6d73", "#b5ff8c"];
  for (let i = 0; i < 22; i += 1) {
    const chip = document.createElement("span");
    chip.className = "confetti";
    chip.style.left = `${Math.random() * 100}%`;
    chip.style.background = colors[Math.floor(Math.random() * colors.length)];
    chip.style.animationDelay = `${Math.random() * 0.2}s`;
    chip.style.transform = `rotate(${Math.random() * 260}deg)`;
    els.celebrationLayer.appendChild(chip);
    window.setTimeout(() => chip.remove(), 1400);
  }
  els.milestonePanel.classList.add("pulse");
  window.setTimeout(() => {
    els.milestonePanel.classList.remove("pulse");
  }, 700);
  showToast(`Milestone unlocked: ${label}`);
}

function maybeCelebrateMilestone(previousScore, currentScore) {
  if (!Number.isFinite(previousScore)) {
    return;
  }
  const unlocked = MILESTONES.filter(
    (milestone) => previousScore < milestone.threshold && currentScore >= milestone.threshold
  );
  if (!unlocked.length) {
    return;
  }
  unlocked.forEach((milestone, index) => {
    window.setTimeout(() => triggerCelebration(milestone.label), index * 160);
  });
  addTimeline(`Milestone unlocked: ${unlocked.map((item) => item.label).join(", ")}`);
}

function clearTourFocus() {
  document.querySelectorAll(".tour-focus").forEach((node) => {
    node.classList.remove("tour-focus");
  });
}

function renderTourSteps(activeIndex = -1) {
  els.tourSteps.innerHTML = "";
  TOUR_FLOW.forEach((step, index) => {
    const li = document.createElement("li");
    if (index < activeIndex) {
      li.classList.add("done");
    } else if (index === activeIndex) {
      li.classList.add("active");
    }
    li.innerHTML = `<strong>${step.label}</strong><span>${step.note}</span>`;
    els.tourSteps.appendChild(li);
  });
}

function updateTourButtons() {
  els.startTourBtn.disabled = state.tourRunning || state.loading;
  els.stopTourBtn.disabled = !state.tourRunning;
}

function stepTour(index) {
  const step = TOUR_FLOW[index];
  if (!step) {
    stopTour(true);
    return;
  }

  state.tourIndex = index;
  clearTourFocus();
  renderTourSteps(index);

  const target = document.getElementById(step.target);
  if (target) {
    target.classList.add("tour-focus");
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  const progress = ((index + 1) / TOUR_FLOW.length) * 100;
  els.tourProgressBar.style.width = `${progress}%`;
  addTimeline(`[Tour] ${step.label}`);
}

function startTour() {
  if (state.tourRunning || state.loading) {
    return;
  }
  state.tourRunning = true;
  state.tutorialTourSeen = true;
  state.tourIndex = -1;
  renderTutorial();
  updateTourButtons();
  stepTour(0);
  state.tourTimer = window.setInterval(() => {
    const next = state.tourIndex + 1;
    if (next >= TOUR_FLOW.length) {
      stopTour(true);
      return;
    }
    stepTour(next);
  }, 2500);
}

function stopTour(completed = false) {
  if (state.tourTimer) {
    window.clearInterval(state.tourTimer);
    state.tourTimer = null;
  }
  state.tourRunning = false;
  if (!completed) {
    clearTourFocus();
    renderTourSteps(-1);
    els.tourProgressBar.style.width = "0%";
    addTimeline("Demo tour stopped.");
  } else {
    clearTourFocus();
    renderTourSteps(TOUR_FLOW.length);
    addTimeline("Demo tour complete.");
    showToast("Demo tour complete");
  }
  updateTourButtons();
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

async function runAction(action) {
  const path = els.projectPath.value.trim();
  if (!path) {
    showToast("Project path is required.");
    return;
  }

  persistPath();
  setLoading(true);
  updateTourButtons();
  addTimeline(`Starting ${action}...`);

  try {
    const endpoint = {
      audit: "/api/audit",
      pack: "/api/agent-pack",
      coach: "/api/coach",
      roadmap: "/api/roadmap",
      ship: "/api/ship",
    }[action];

    if (!endpoint) {
      throw new Error(`Unknown action: ${action}`);
    }

    const payload = { project_path: path };
    if (action === "coach") {
      payload.apply_safe = false;
    }
    if (action === "ship") {
      payload.apply_safe = Boolean(els.applySafeToggle.checked);
    }

    const data = await postJSON(endpoint, payload);
    const report = data.report || data.after;
    const insights = data.insights || data.after_insights;
    const improvement = typeof data.improvement === "number" ? data.improvement : null;

    const previousScore = state.lastScore;
    const nextScore = Number(report?.scorecard?.overall || 0);

    state.report = report;
    state.insights = insights;
    state.tasks = data.agent_tasks || [];
    state.lastScore = nextScore;

    updateScoreCard(report, insights, improvement);
    renderBreakdown(insights);
    renderFindings(report);
    renderTaskQueue(state.tasks);
    renderArtifacts(data.artifacts || {});
    renderSimulator(report);
    renderMilestones(nextScore);
    maybeCelebrateMilestone(previousScore, nextScore);
    renderTutorial();

    const preview =
      data.agent_pack_markdown ||
      data.coach_markdown ||
      data.roadmap_markdown ||
      JSON.stringify(report?.scorecard || {}, null, 2);
    setPreview(`${action.toUpperCase()} Output`, preview);

    updateHistory(action, nextScore, improvement);

    if (action === "ship") {
      addTimeline(
        `Ship complete. Score delta ${improvement >= 0 ? "+" : ""}${Number(improvement || 0).toFixed(1)}.`
      );
    } else {
      addTimeline(`${action} complete.`);
    }
    showToast(`${action} completed successfully`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    addTimeline(`Error: ${message}`);
    showToast(message);
  } finally {
    setLoading(false);
    updateTourButtons();
    renderTutorial();
  }
}

function wireEvents() {
  els.auditBtn.addEventListener("click", () => runAction("audit"));
  els.packBtn.addEventListener("click", () => runAction("pack"));
  els.coachBtn.addEventListener("click", () => runAction("coach"));
  els.roadmapBtn.addEventListener("click", () => runAction("roadmap"));
  els.shipBtn.addEventListener("click", () => runAction("ship"));
  els.tutorialStartBtn.addEventListener("click", () => {
    state.tutorialStarted = true;
    renderTutorial();
    const { firstIncomplete } = tutorialProgressStats();
    if (firstIncomplete) {
      focusTutorialTarget(firstIncomplete.target);
      showToast(firstIncomplete.hint);
    }
  });
  els.tutorialNextBtn.addEventListener("click", () => {
    runTutorialNextStep();
  });
  els.toggleAdvancedBtn.addEventListener("click", () => {
    setAdvancedActionsVisible(!state.uiShowAdvanced);
  });
  els.projectPath.addEventListener("blur", persistPath);
  els.projectPath.addEventListener("input", () => renderTutorial());

  els.copyPreviewBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(els.previewContent.textContent || "");
      showToast("Preview copied to clipboard");
    } catch {
      showToast("Clipboard copy failed");
    }
  });

  els.clearHistoryBtn.addEventListener("click", () => {
    state.history = [];
    renderHistory();
    renderTutorial();
    addTimeline("Run history cleared.");
  });

  els.startTourBtn.addEventListener("click", startTour);
  els.stopTourBtn.addEventListener("click", () => stopTour(false));
}

function init() {
  restorePath();
  wireEvents();
  setAdvancedActionsVisible(false);
  renderHistory();
  renderTourSteps(-1);
  renderMilestones(Number.NaN);
  updateSimulatorMetrics();
  renderTutorial();
  updateTourButtons();
  addTimeline("Studio ready.");
}

init();
