const navButtons = document.querySelectorAll("[data-view-target]");
const views = document.querySelectorAll("[data-view]");
const typeSelect = document.querySelector("[data-case-type]");
const typePanels = document.querySelectorAll("[data-type-panel]");

const taskModal = document.getElementById("run-modal");
const taskForm = document.getElementById("run-form");
const taskCaseSetSelect = document.querySelector("[data-task-case-set-select]");
const taskMetricSelect = document.querySelector("[data-task-metric-select]");
const openTaskModalButton = document.querySelector("[data-open-run-modal]");
const closeTaskModalButtons = document.querySelectorAll("[data-close-run-modal]");
const taskError = document.querySelector("[data-run-error]");
const taskSubmit = document.querySelector("[data-run-submit]");

const scheduleModal = document.getElementById("schedule-modal");
const scheduleForm = document.getElementById("schedule-form");
const openScheduleModalButton = document.querySelector("[data-open-schedule-modal]");
const closeScheduleModalButtons = document.querySelectorAll("[data-close-schedule-modal]");
const scheduleError = document.querySelector("[data-schedule-error]");
const scheduleSubmit = document.querySelector("[data-schedule-submit]");
const scheduleTaskSelect = document.querySelector("[data-schedule-task-select]");
const scheduleTypeSelect = document.querySelector("[data-schedule-type-select]");
const runAtField = document.querySelector("[data-run-at-field]");
const dailyTimeField = document.querySelector("[data-daily-time-field]");

const taskTableBody = document.querySelector("[data-task-table-body]");
const scheduleTableBody = document.querySelector("[data-schedule-table-body]");

const taskDetailHeading = document.querySelector("[data-task-detail-heading]");
const taskDetailCaseCount = document.querySelector("[data-task-detail-case-count]");
const taskDetailLaunchMode = document.querySelector("[data-task-detail-launch-mode]");
const taskDetailStatus = document.querySelector("[data-task-detail-status]");
const taskDetailCaseSet = document.querySelector("[data-task-detail-case-set]");
const taskDetailEnvironment = document.querySelector("[data-task-detail-environment]");
const taskDetailMetricSet = document.querySelector("[data-task-detail-metric-set]");
const taskDetailScheduleName = document.querySelector("[data-task-detail-schedule-name]");
const taskDetailProgressValue = document.querySelector("[data-task-detail-progress-value]");
const taskDetailProgressFill = document.querySelector("[data-task-detail-progress-fill]");
const taskDetailAccuracy = document.querySelector("[data-task-detail-accuracy]");
const taskDetailRepeatCount = document.querySelector("[data-task-detail-repeat-count]");
const taskDetailScheduleCard = document.querySelector("[data-task-detail-schedule-card]");
const taskDetailLatestRunTime = document.querySelector("[data-task-detail-latest-run-time]");
const taskDetailTriggerSource = document.querySelector("[data-task-detail-trigger-source]");
const taskHistoryBody = document.querySelector("[data-task-history-body]");
const executeTaskButton = document.querySelector("[data-execute-task]");

const caseSetsView = document.querySelector('[data-view="case-sets"]');
const caseSetCards = document.querySelectorAll(".set-card[data-case-set-id]");
const defaultCaseSetActions = document.querySelector("[data-default-case-set-actions]");
const exportToolbar = document.querySelector("[data-export-toolbar]");
const exportCount = document.querySelector("[data-export-count]");
const enterExportModeButton = document.querySelector("[data-enter-export-mode]");
const exportSelectedButton = document.querySelector("[data-export-selected]");
const cancelExportButton = document.querySelector("[data-cancel-export]");
const caseSetHeading = document.querySelector("[data-case-set-heading]");
const caseSetTypeChip = document.querySelector("[data-case-set-type-chip]");
const caseSetCountChip = document.querySelector("[data-case-set-count-chip]");
const caseSetStatusChip = document.querySelector("[data-case-set-status-chip]");
const caseSetFeedback = document.querySelector("[data-case-set-feedback]");
const caseListBody = document.querySelector("[data-case-list-body]");
const updateCaseSetButton = document.querySelector("[data-update-case-set]");
const exportCurrentCaseSetButton = document.querySelector("[data-export-current-case-set]");
const caseSetFileInput = document.querySelector("[data-case-set-file-input]");

const metricSummaryCount = document.querySelector("[data-metric-summary-count]");
const metricSummaryScenarios = document.querySelector("[data-metric-summary-scenarios]");
const metricSummaryHardGates = document.querySelector("[data-metric-summary-hard-gates]");
const metricFilterButtons = document.querySelectorAll("[data-metric-filter]");
const metricSetList = document.querySelector("[data-metric-set-list]");
const metricSetDetail = document.querySelector("[data-metric-set-detail]");
const metricDetailName = document.querySelector("[data-metric-detail-name]");
const metricDetailScenario = document.querySelector("[data-metric-detail-scenario]");
const metricDetailThreshold = document.querySelector("[data-metric-detail-threshold]");
const metricDetailDescription = document.querySelector("[data-metric-detail-description]");
const metricDetailFormula = document.querySelector("[data-metric-detail-formula]");
const metricDetailHardGateCount = document.querySelector("[data-metric-detail-hard-gate-count]");
const metricBenchmarkList = document.querySelector("[data-metric-benchmark-list]");
const metricDimensionBody = document.querySelector("[data-metric-dimension-body]");
const openMetricModalButton = document.querySelector("[data-open-metric-modal]");
const editMetricSetButton = document.querySelector("[data-edit-metric-set]");
const metricModal = document.getElementById("metric-modal");
const metricForm = document.getElementById("metric-form");
const closeMetricModalButtons = document.querySelectorAll("[data-close-metric-modal]");
const metricModalTitle = document.querySelector("[data-metric-modal-title]");
const metricTemplateSelect = document.querySelector("[data-metric-template-select]");
const metricFormName = document.querySelector("[data-metric-form-name]");
const metricFormScenario = document.querySelector("[data-metric-form-scenario]");
const metricFormDescription = document.querySelector("[data-metric-form-description]");
const metricFormThreshold = document.querySelector("[data-metric-form-threshold]");
const metricEditBody = document.querySelector("[data-metric-edit-body]");
const metricError = document.querySelector("[data-metric-error]");
const metricSubmitButton = document.querySelector("[data-metric-submit]");

const difficultyLabels = ["低", "中", "高"];
const launchModeLabels = { immediate: "立即执行", deferred: "待执行" };
const taskStatusLabels = { pending: "待执行", scheduled: "已定时", running: "执行中", succeeded: "已完成", failed: "失败" };
const scheduleTypeLabels = { one_time: "单次", daily: "每日" };
const scheduleStatusLabels = { enabled: "启用", paused: "暂停", completed: "已完成" };
const triggerSourceLabels = {
  immediate_create: "创建即执行",
  manual: "手动执行",
  schedule: "定时触发",
  legacy: "历史记录",
};

let currentCaseSetId = "cs-nl2sql";
let currentCaseSetDetail = null;
let exportMode = false;
const selectedCaseSetIds = new Set();

let tasksState = [];
let schedulesState = [];
let currentTaskId = null;
let currentTaskDetail = null;
let metricSetsState = [];
let currentMetricSetId = "metric-nl2sql-exec";
let currentMetricFilter = "全部";
let metricModalMode = "create";

const caseSetTypeMap = {
  "cs-seed": "NL2SQL",
  "cs-nl2sql": "NL2SQL",
  "cs-nl2chart": "NL2CHART",
  "cs-smart-qa": "智能问数",
  "cs-report": "报告多轮交互",
};

function activateView(target) {
  views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === target);
  });
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === target);
  });
  if (target !== "case-sets") {
    setExportMode(false);
  }
}

function activateTypePanel(type) {
  typePanels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.typePanel === type);
  });
}

function formatDateTime(value) {
  if (!value) {
    return "未执行";
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const pad = (part) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return map[char];
  });
}

function labelFor(map, value, fallback = "-") {
  return map[value] || value || fallback;
}

function statusChip(value, labelMap) {
  const label = labelFor(labelMap, value, "-");
  return `<span class="status-chip ${escapeHtml(value || "")}">${escapeHtml(label)}</span>`;
}

function progressMeta(execution) {
  if (!execution) {
    return { text: "未执行", percent: 0, accuracy: "未执行", lastRunTime: "未执行" };
  }
  const total = Number(execution.total_cases || 0);
  const executed = Number(execution.executed_cases || 0);
  const percent = total > 0 ? Math.max(0, Math.min(100, Math.round((executed / total) * 100))) : 0;
  const accuracy = `${Math.round(Number(execution.accuracy || 0) * 100)}%`;
  return {
    text: `${executed} / ${total}`,
    percent,
    accuracy,
    lastRunTime: formatDateTime(execution.started_at),
  };
}

function renderProgressCell(execution) {
  const meta = progressMeta(execution);
  return `
    <div class="progress-cell">
      <span class="progress-text">${escapeHtml(meta.text)}</span>
      <div class="progress-bar" aria-label="进度条">
        <div class="progress-fill" style="width: ${meta.percent}%"></div>
      </div>
    </div>
  `;
}

function openTaskModal() {
  if (!taskModal) {
    return;
  }
  populateTaskMetricOptions(taskCaseSetSelect?.value || "cs-nl2sql");
  taskModal.classList.remove("hidden");
  if (taskError) {
    taskError.classList.add("hidden");
  }
}

function closeTaskModal() {
  if (!taskModal) {
    return;
  }
  taskModal.classList.add("hidden");
  if (taskForm) {
    taskForm.reset();
  }
  if (taskError) {
    taskError.classList.add("hidden");
    taskError.textContent = "请填写所有必填项";
  }
}

function showTaskError(message) {
  if (!taskError) {
    return;
  }
  taskError.textContent = message;
  taskError.classList.remove("hidden");
}

function openScheduleModal() {
  if (!scheduleModal) {
    return;
  }
  populateScheduleTaskOptions();
  syncScheduleTypeFields(scheduleTypeSelect?.value || "one_time");
  scheduleModal.classList.remove("hidden");
  if (scheduleError) {
    scheduleError.classList.add("hidden");
  }
}

function closeScheduleModal() {
  if (!scheduleModal) {
    return;
  }
  scheduleModal.classList.add("hidden");
  if (scheduleForm) {
    scheduleForm.reset();
  }
  if (scheduleError) {
    scheduleError.classList.add("hidden");
    scheduleError.textContent = "请填写所有必填项";
  }
  syncScheduleTypeFields("one_time");
}

function showScheduleError(message) {
  if (!scheduleError) {
    return;
  }
  scheduleError.textContent = message;
  scheduleError.classList.remove("hidden");
}

function showCaseSetFeedback(message, isError = false) {
  if (!caseSetFeedback) {
    return;
  }
  caseSetFeedback.textContent = message;
  caseSetFeedback.classList.remove("hidden");
  caseSetFeedback.classList.toggle("error", isError);
}

function clearCaseSetFeedback() {
  if (!caseSetFeedback) {
    return;
  }
  caseSetFeedback.classList.add("hidden");
  caseSetFeedback.classList.remove("error");
  caseSetFeedback.textContent = "";
}

function syncExportSelection() {
  caseSetCards.forEach((card) => {
    const caseSetId = card.dataset.caseSetId;
    const isSelected = selectedCaseSetIds.has(caseSetId);
    card.classList.toggle("selected", isSelected);
    const checkbox = card.querySelector("[data-case-set-check]");
    if (checkbox) {
      checkbox.checked = isSelected;
    }
  });
  if (exportCount) {
    exportCount.textContent = String(selectedCaseSetIds.size);
  }
  if (exportSelectedButton) {
    exportSelectedButton.disabled = selectedCaseSetIds.size === 0;
  }
}

function setExportMode(enabled) {
  exportMode = enabled;
  if (caseSetsView) {
    caseSetsView.classList.toggle("export-mode", enabled);
  }
  if (defaultCaseSetActions) {
    defaultCaseSetActions.classList.toggle("hidden", enabled);
  }
  if (exportToolbar) {
    exportToolbar.classList.toggle("hidden", !enabled);
  }
  if (!enabled) {
    selectedCaseSetIds.clear();
  }
  syncExportSelection();
}

function toggleCaseSetSelection(caseSetId) {
  if (!caseSetId) {
    return;
  }
  if (selectedCaseSetIds.has(caseSetId)) {
    selectedCaseSetIds.delete(caseSetId);
  } else {
    selectedCaseSetIds.add(caseSetId);
  }
  syncExportSelection();
}

function parseFilename(headerValue, fallbackName) {
  if (!headerValue) {
    return fallbackName;
  }
  const utfMatch = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
  if (utfMatch) {
    return decodeURIComponent(utfMatch[1]);
  }
  const simpleMatch = headerValue.match(/filename="?([^";]+)"?/i);
  return simpleMatch ? simpleMatch[1] : fallbackName;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "request_failed");
  }
  return payload;
}

async function downloadCaseSet(caseSetId, fallbackName) {
  const response = await fetch(`/api/case-sets/${encodeURIComponent(caseSetId)}/export`);
  if (!response.ok) {
    throw new Error("download_failed");
  }
  const blob = await response.blob();
  const filename = parseFilename(response.headers.get("content-disposition"), fallbackName);
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 0);
}

async function createTask(payload) {
  return requestJson("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function fetchTasks() {
  return requestJson("/api/tasks");
}

async function fetchTaskDetail(taskId) {
  return requestJson(`/api/tasks/${encodeURIComponent(taskId)}`);
}

async function executeTask(taskId) {
  return requestJson(`/api/tasks/${encodeURIComponent(taskId)}/execute`, { method: "POST" });
}

async function createSchedule(payload) {
  return requestJson("/api/schedules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function fetchSchedules() {
  return requestJson("/api/schedules");
}

async function fetchCaseSetDetail(caseSetId) {
  return requestJson(`/api/case-sets/${encodeURIComponent(caseSetId)}`);
}

async function fetchMetricSets() {
  return requestJson("/api/metric-sets");
}

async function createMetricSet(payload) {
  return requestJson("/api/metric-sets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function updateMetricSet(metricSetId, payload) {
  return requestJson(`/api/metric-sets/${encodeURIComponent(metricSetId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function importCaseSetFile(caseSetId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`/api/case-sets/${encodeURIComponent(caseSetId)}/import`, {
    method: "POST",
    body: formData,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "导入失败");
  }
  return payload;
}

function buildCaseRow(caseItem, index, isSeed) {
  const difficulty = difficultyLabels[index % difficultyLabels.length];
  const status = isSeed ? "不可评测" : "待评测";
  return `
    <tr class="row-link" data-view-link="case-detail">
      <td>${escapeHtml(caseItem.case_id)}</td>
      <td>${escapeHtml(caseItem.title || caseItem.case_id)}</td>
      <td>${escapeHtml(difficulty)}</td>
      <td>${escapeHtml(status)}</td>
      <td class="strong">-</td>
    </tr>
  `;
}

function updateCaseSetCardMeta(caseSet, count) {
  const card = document.querySelector(`.set-card[data-case-set-id="${caseSet.id}"]`);
  if (!card) {
    return;
  }
  card.dataset.caseSetName = caseSet.name;
  card.dataset.caseSetType = caseSet.type;
  const meta = card.querySelector(".set-meta");
  if (meta) {
    meta.textContent = `类型：${caseSet.type} · ${count} 用例`;
  }
}

function renderCaseSetDetail(detail) {
  const caseSet = detail.case_set;
  const cases = detail.cases || [];
  currentCaseSetDetail = detail;
  if (caseSetHeading) {
    caseSetHeading.textContent = `用例列表：${caseSet.name}`;
  }
  if (caseSetTypeChip) {
    caseSetTypeChip.textContent = caseSet.type;
  }
  if (caseSetCountChip) {
    caseSetCountChip.textContent = `${cases.length} 个用例`;
  }
  if (caseSetStatusChip) {
    caseSetStatusChip.textContent = caseSet.is_seed ? "种子，不可评测" : "可导出，可评测";
  }
  if (caseListBody) {
    if (cases.length === 0) {
      caseListBody.innerHTML = `
        <tr>
          <td colspan="5">当前用例集暂无用例</td>
        </tr>
      `;
    } else {
      caseListBody.innerHTML = cases.map((caseItem, index) => buildCaseRow(caseItem, index, caseSet.is_seed)).join("");
    }
  }
  updateCaseSetCardMeta(caseSet, cases.length);
}

async function loadCaseSetDetail(caseSetId, options = {}) {
  const requestedCaseSetId = caseSetId || currentCaseSetId;
  const preserveFeedback = Boolean(options.preserveFeedback);
  currentCaseSetId = requestedCaseSetId;
  if (!preserveFeedback) {
    clearCaseSetFeedback();
  }
  try {
    const detail = await fetchCaseSetDetail(requestedCaseSetId);
    if (requestedCaseSetId !== currentCaseSetId) {
      return null;
    }
    renderCaseSetDetail(detail);
    return detail;
  } catch (error) {
    if (requestedCaseSetId === currentCaseSetId) {
      showCaseSetFeedback("加载用例集失败，请稍后重试", true);
    }
    return null;
  }
}

function populateScheduleTaskOptions() {
  if (!scheduleTaskSelect) {
    return;
  }
  const availableTasks = tasksState.filter(
    (task) => task.launch_mode === "deferred" && (!task.schedule || task.schedule.schedule_status !== "enabled"),
  );
  if (availableTasks.length === 0) {
    scheduleTaskSelect.innerHTML = '<option value="">暂无可关联的待执行任务</option>';
    return;
  }
  scheduleTaskSelect.innerHTML = '<option value="">请选择待执行任务</option>' + availableTasks
    .map((task) => `<option value="${escapeHtml(task.task_id)}">${escapeHtml(task.name)}</option>`)
    .join("");
}

function getMetricSetById(metricSetId) {
  return metricSetsState.find((item) => item.metric_set_id === metricSetId) || null;
}

function countHardGates(metricSet) {
  return (metricSet?.dimensions || []).filter((item) => item.hard_gate).length;
}

function scenarioMatchesFilter(metricSet) {
  return currentMetricFilter === "全部" || metricSet.scenario_type === currentMetricFilter;
}

function renderMetricSummaries(metricSets) {
  if (metricSummaryCount) {
    metricSummaryCount.textContent = String(metricSets.length);
  }
  if (metricSummaryScenarios) {
    const scenarioCount = new Set(metricSets.map((item) => item.scenario_type)).size;
    metricSummaryScenarios.textContent = String(scenarioCount);
  }
  if (metricSummaryHardGates) {
    const totalHardGates = metricSets.reduce((sum, item) => sum + countHardGates(item), 0);
    metricSummaryHardGates.textContent = String(totalHardGates);
  }
}

function renderMetricSetList(metricSets) {
  if (!metricSetList) {
    return;
  }
  if (metricSets.length === 0) {
    metricSetList.innerHTML = '<div class="metric-empty">当前筛选条件下暂无指标参数集</div>';
    return;
  }
  metricSetList.innerHTML = metricSets
    .map(
      (metricSet) => `
        <button class="metric-set-card ${metricSet.metric_set_id === currentMetricSetId ? "active" : ""}" type="button" data-metric-set-card="${escapeHtml(metricSet.metric_set_id)}">
          <div class="metric-set-card-top">
            <span class="chip">${escapeHtml(metricSet.scenario_type)}</span>
            <span class="metric-score-chip">门槛 ${escapeHtml(Number(metricSet.pass_threshold).toFixed(2))}</span>
          </div>
          <div class="metric-set-card-title">${escapeHtml(metricSet.name)}</div>
          <div class="metric-set-card-desc">${escapeHtml(metricSet.description)}</div>
        </button>
      `,
    )
    .join("");
}

function renderMetricSetDetail(metricSet) {
  if (!metricSetDetail || !metricSet) {
    return;
  }
  if (metricDetailName) {
    metricDetailName.textContent = metricSet.name;
  }
  if (metricDetailScenario) {
    metricDetailScenario.textContent = metricSet.scenario_type;
  }
  if (metricDetailThreshold) {
    metricDetailThreshold.textContent = `发布门槛 ${Number(metricSet.pass_threshold).toFixed(2)}`;
  }
  if (metricDetailDescription) {
    metricDetailDescription.textContent = metricSet.description;
  }
  if (metricDetailFormula) {
    metricDetailFormula.textContent = metricSet.score_formula;
  }
  if (metricDetailHardGateCount) {
    metricDetailHardGateCount.textContent = String(countHardGates(metricSet));
  }
  if (metricBenchmarkList) {
    metricBenchmarkList.innerHTML = (metricSet.benchmark_refs || [])
      .map(
        (item) => `
          <a class="metric-benchmark-item" href="${escapeHtml(item.url || "#")}" target="_blank" rel="noreferrer">
            <strong>${escapeHtml(item.title || "-")}</strong>
            <span>${escapeHtml(item.note || "")}</span>
          </a>
        `,
      )
      .join("");
  }
  if (metricDimensionBody) {
    metricDimensionBody.innerHTML = (metricSet.dimensions || [])
      .map(
        (item) => `
          <tr>
            <td>${escapeHtml(item.name)}</td>
            <td>${escapeHtml(item.measurement)}</td>
            <td>${escapeHtml(Number(item.weight).toFixed(2))}</td>
            <td>${escapeHtml(Number(item.target).toFixed(2))}</td>
            <td>${escapeHtml(item.hard_gate ? "是" : "否")}</td>
            <td>${escapeHtml(item.business_value)}</td>
          </tr>
        `,
      )
      .join("");
  }
}

function refreshMetricPage() {
  const filteredMetricSets = metricSetsState.filter(scenarioMatchesFilter);
  if (!filteredMetricSets.some((item) => item.metric_set_id === currentMetricSetId)) {
    currentMetricSetId = filteredMetricSets[0]?.metric_set_id || null;
  }
  renderMetricSummaries(metricSetsState);
  renderMetricSetList(filteredMetricSets);
  renderMetricSetDetail(getMetricSetById(currentMetricSetId));
}

function buildMetricEditRows(dimensions) {
  if (!metricEditBody) {
    return;
  }
  metricEditBody.innerHTML = (dimensions || [])
    .map(
      (item) => `
        <tr data-metric-dimension-row="${escapeHtml(item.key)}">
          <td>
            <span class="metric-edit-label">${escapeHtml(item.name)}</span>
            <div class="metric-inline-meta">${escapeHtml(item.key)}</div>
          </td>
          <td>${escapeHtml(item.measurement)}</td>
          <td>
            <input class="filter-input" type="number" step="0.01" min="0" value="${escapeHtml(item.weight)}" data-dimension-field="weight" />
          </td>
          <td>
            <input class="filter-input" type="number" step="0.01" min="0" max="1" value="${escapeHtml(item.target)}" data-dimension-field="target" />
          </td>
          <td>
            <input type="checkbox" ${item.hard_gate ? "checked" : ""} data-dimension-field="hard_gate" />
            <div class="metric-edit-help">${escapeHtml(item.business_value)}</div>
          </td>
        </tr>
      `,
    )
    .join("");
}

function readMetricDimensionsFromForm(baseMetricSet) {
  return (baseMetricSet?.dimensions || []).map((item) => {
    const row = metricEditBody?.querySelector(`[data-metric-dimension-row="${CSS.escape(item.key)}"]`);
    const weightInput = row?.querySelector('[data-dimension-field="weight"]');
    const targetInput = row?.querySelector('[data-dimension-field="target"]');
    const hardGateInput = row?.querySelector('[data-dimension-field="hard_gate"]');
    return {
      ...item,
      weight: Number.parseFloat(weightInput?.value || String(item.weight)),
      target: Number.parseFloat(targetInput?.value || String(item.target)),
      hard_gate: Boolean(hardGateInput?.checked),
    };
  });
}

function populateMetricTemplateOptions() {
  if (!metricTemplateSelect) {
    return;
  }
  metricTemplateSelect.innerHTML = metricSetsState
    .map((item) => `<option value="${escapeHtml(item.metric_set_id)}">${escapeHtml(item.name)}</option>`)
    .join("");
}

function populateTaskMetricOptions(caseSetId) {
  if (!taskMetricSelect) {
    return;
  }
  const caseSetType = caseSetTypeMap[caseSetId] || null;
  const availableMetricSets = metricSetsState.filter((item) => !caseSetType || item.scenario_type === "通用" || item.scenario_type === caseSetType);
  taskMetricSelect.innerHTML = '<option value="">请选择</option>' + availableMetricSets
    .map((item) => `<option value="${escapeHtml(item.metric_set_id)}">${escapeHtml(item.name)}</option>`)
    .join("");
  if (availableMetricSets.length > 0) {
    taskMetricSelect.value = availableMetricSets[0].metric_set_id;
  }
}

function openMetricModal(mode = "create") {
  if (!metricModal) {
    return;
  }
  metricModalMode = mode;
  const currentMetricSet = getMetricSetById(currentMetricSetId) || metricSetsState[0] || null;
  if (metricModalTitle) {
    metricModalTitle.textContent = mode === "edit" ? "编辑参数组合" : "新增参数组合";
  }
  if (metricError) {
    metricError.classList.add("hidden");
  }
  populateMetricTemplateOptions();
  const seedMetricSet = mode === "edit" ? currentMetricSet : currentMetricSet;
  if (metricTemplateSelect && seedMetricSet) {
    metricTemplateSelect.value = seedMetricSet.metric_set_id;
    metricTemplateSelect.disabled = mode === "edit";
  }
  if (metricFormName && seedMetricSet) {
    metricFormName.value = mode === "edit" ? seedMetricSet.name : `${seedMetricSet.name} - 自定义`;
  }
  if (metricFormScenario && seedMetricSet) {
    metricFormScenario.value = seedMetricSet.scenario_type;
  }
  if (metricFormDescription && seedMetricSet) {
    metricFormDescription.value = seedMetricSet.description;
  }
  if (metricFormThreshold && seedMetricSet) {
    metricFormThreshold.value = String(seedMetricSet.pass_threshold);
  }
  buildMetricEditRows(seedMetricSet?.dimensions || []);
  metricModal.classList.remove("hidden");
}

function closeMetricModal() {
  if (!metricModal) {
    return;
  }
  metricModal.classList.add("hidden");
  if (metricForm) {
    metricForm.reset();
  }
  if (metricError) {
    metricError.classList.add("hidden");
    metricError.textContent = "请填写所有必填项";
  }
  if (metricTemplateSelect) {
    metricTemplateSelect.disabled = false;
  }
}

function showMetricError(message) {
  if (!metricError) {
    return;
  }
  metricError.textContent = message;
  metricError.classList.remove("hidden");
}

function renderTasks(tasks) {
  if (!taskTableBody) {
    return;
  }
  if (tasks.length === 0) {
    taskTableBody.innerHTML = `
      <tr>
        <td colspan="10">当前暂无评测任务</td>
      </tr>
    `;
    return;
  }
  taskTableBody.innerHTML = tasks
    .map((task) => {
      const latestExecution = task.latest_execution;
      const progress = progressMeta(latestExecution);
      return `
        <tr class="row-link" data-view-link="run-detail" data-task-id="${escapeHtml(task.task_id)}">
          <td>${escapeHtml(task.name)}</td>
          <td>${escapeHtml(labelFor(launchModeLabels, task.launch_mode))}</td>
          <td>${statusChip(task.task_status, taskStatusLabels)}</td>
          <td>${escapeHtml(task.case_set_id)}</td>
          <td>${escapeHtml(task.environment_id)}</td>
          <td>${escapeHtml(task.metric_set?.name || task.metric_set_id)}</td>
          <td>${escapeHtml(task.schedule?.name || "-")}</td>
          <td>${escapeHtml(progress.lastRunTime)}</td>
          <td>${renderProgressCell(latestExecution)}</td>
          <td class="strong">${escapeHtml(latestExecution ? progress.accuracy : "-")}</td>
        </tr>
      `;
    })
    .join("");
}

function renderSchedules(schedules) {
  if (!scheduleTableBody) {
    return;
  }
  if (schedules.length === 0) {
    scheduleTableBody.innerHTML = `
      <tr>
        <td colspan="6">当前暂无定时任务</td>
      </tr>
    `;
    return;
  }
  scheduleTableBody.innerHTML = schedules
    .map(
      (schedule) => `
        <tr>
          <td>${escapeHtml(schedule.name)}</td>
          <td>${escapeHtml(schedule.task?.name || "-")}</td>
          <td>${escapeHtml(labelFor(scheduleTypeLabels, schedule.schedule_type))}</td>
          <td>${escapeHtml(formatDateTime(schedule.next_triggered_at))}</td>
          <td>${escapeHtml(formatDateTime(schedule.last_triggered_at))}</td>
          <td>${statusChip(schedule.schedule_status, scheduleStatusLabels)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderTaskDetail(detail) {
  currentTaskDetail = detail;
  const { task, latest_execution: latestExecution, execution_history: history, schedule, metric_set: metricSet } = detail;
  const progress = progressMeta(latestExecution);
  if (taskDetailHeading) {
    taskDetailHeading.textContent = `任务详情：${task.name}`;
  }
  if (taskDetailCaseCount) {
    taskDetailCaseCount.textContent = latestExecution ? progress.text : "未执行";
  }
  if (taskDetailLaunchMode) {
    taskDetailLaunchMode.textContent = labelFor(launchModeLabels, task.launch_mode);
  }
  if (taskDetailStatus) {
    taskDetailStatus.textContent = labelFor(taskStatusLabels, task.task_status);
  }
  if (taskDetailCaseSet) {
    taskDetailCaseSet.textContent = task.case_set_id;
  }
  if (taskDetailEnvironment) {
    taskDetailEnvironment.textContent = task.environment_id;
  }
  if (taskDetailMetricSet) {
    taskDetailMetricSet.textContent = metricSet?.name || task.metric_set_id;
  }
  if (taskDetailScheduleName) {
    taskDetailScheduleName.textContent = schedule?.name || "未关联";
  }
  if (taskDetailProgressValue) {
    taskDetailProgressValue.textContent = latestExecution ? progress.text : "未执行";
  }
  if (taskDetailProgressFill) {
    taskDetailProgressFill.style.width = `${progress.percent}%`;
  }
  if (taskDetailAccuracy) {
    taskDetailAccuracy.textContent = latestExecution ? progress.accuracy : "未执行";
  }
  if (taskDetailRepeatCount) {
    taskDetailRepeatCount.value = String(task.repeat_count);
  }
  if (taskDetailLatestRunTime) {
    taskDetailLatestRunTime.textContent = latestExecution ? formatDateTime(latestExecution.started_at) : "未执行";
  }
  if (taskDetailTriggerSource) {
    taskDetailTriggerSource.textContent = latestExecution ? labelFor(triggerSourceLabels, latestExecution.trigger_source) : "未执行";
  }
  if (executeTaskButton) {
    executeTaskButton.classList.toggle("hidden", task.launch_mode !== "deferred");
    executeTaskButton.dataset.taskId = task.task_id;
  }
  if (taskDetailScheduleCard) {
    if (schedule) {
      taskDetailScheduleCard.innerHTML = `
        <div class="analysis-label">${escapeHtml(schedule.name)}</div>
        <div class="analysis-value">${escapeHtml(labelFor(scheduleTypeLabels, schedule.schedule_type))}</div>
        <div class="detail-note">下次执行：${escapeHtml(formatDateTime(schedule.next_triggered_at))}</div>
        <div class="detail-note">状态：${escapeHtml(labelFor(scheduleStatusLabels, schedule.schedule_status))}</div>
      `;
    } else {
      taskDetailScheduleCard.innerHTML = `
        <div class="analysis-label">当前暂无定时任务</div>
        <div class="analysis-value">未关联</div>
      `;
    }
  }
  if (taskHistoryBody) {
    if (!history || history.length === 0) {
      taskHistoryBody.innerHTML = `
        <tr>
          <td colspan="6">当前暂无执行记录</td>
        </tr>
      `;
    } else {
      taskHistoryBody.innerHTML = history
        .map((execution) => {
          const executionProgress = progressMeta(execution);
          return `
            <tr>
              <td>${escapeHtml(execution.run_id)}</td>
              <td>${escapeHtml(labelFor(triggerSourceLabels, execution.trigger_source))}</td>
              <td>${statusChip(execution.execution_status, taskStatusLabels)}</td>
              <td>${escapeHtml(formatDateTime(execution.started_at))}</td>
              <td>${escapeHtml(executionProgress.text)}</td>
              <td class="strong">${escapeHtml(executionProgress.accuracy)}</td>
            </tr>
          `;
        })
        .join("");
    }
  }
}

async function loadTasks() {
  try {
    const payload = await fetchTasks();
    tasksState = payload.tasks || [];
    renderTasks(tasksState);
    populateScheduleTaskOptions();
    if (currentTaskId) {
      const existing = tasksState.find((task) => task.task_id === currentTaskId);
      if (!existing) {
        currentTaskId = null;
        currentTaskDetail = null;
      }
    }
  } catch (error) {
    if (taskTableBody) {
      taskTableBody.innerHTML = `
        <tr>
          <td colspan="10">任务加载失败，请稍后重试</td>
        </tr>
      `;
    }
  }
}

async function loadSchedules() {
  try {
    const payload = await fetchSchedules();
    schedulesState = payload.schedules || [];
    renderSchedules(schedulesState);
    populateScheduleTaskOptions();
  } catch (error) {
    if (scheduleTableBody) {
      scheduleTableBody.innerHTML = `
        <tr>
          <td colspan="6">定时任务加载失败，请稍后重试</td>
        </tr>
      `;
    }
  }
}

async function loadMetricSets() {
  try {
    const payload = await fetchMetricSets();
    metricSetsState = payload.metric_sets || [];
    refreshMetricPage();
    populateMetricTemplateOptions();
    populateTaskMetricOptions(taskCaseSetSelect?.value || "cs-nl2sql");
  } catch (error) {
    if (metricSetList) {
      metricSetList.innerHTML = '<div class="metric-empty">指标集加载失败，请稍后重试</div>';
    }
  }
}

async function loadTaskDetail(taskId) {
  currentTaskId = taskId;
  try {
    const detail = await fetchTaskDetail(taskId);
    if (currentTaskId === taskId) {
      renderTaskDetail(detail);
    }
  } catch (error) {
    if (taskDetailHeading) {
      taskDetailHeading.textContent = "任务详情加载失败";
    }
  }
}

function syncScheduleTypeFields(type) {
  if (runAtField) {
    runAtField.classList.toggle("hidden", type !== "one_time");
  }
  if (dailyTimeField) {
    dailyTimeField.classList.toggle("hidden", type !== "daily");
  }
}

if (typeSelect) {
  activateTypePanel(typeSelect.value);
  typeSelect.addEventListener("change", (event) => {
    activateTypePanel(event.target.value);
  });
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activateView(button.dataset.viewTarget);
  });
});

document.addEventListener("click", (event) => {
  const metricCard = event.target.closest("[data-metric-set-card]");
  if (metricCard) {
    currentMetricSetId = metricCard.dataset.metricSetCard || null;
    refreshMetricPage();
    return;
  }

  const link = event.target.closest("[data-view-link]");
  if (!link) {
    return;
  }

  if (link.classList.contains("set-card")) {
    if (exportMode) {
      if (!event.target.closest(".set-select")) {
        toggleCaseSetSelection(link.dataset.caseSetId || "");
      }
      return;
    }
    const caseSetId = link.dataset.caseSetId;
    if (caseSetId) {
      currentCaseSetId = caseSetId;
      void loadCaseSetDetail(caseSetId);
    }
  }

  const taskId = link.dataset.taskId;
  if (taskId) {
    currentTaskId = taskId;
    void loadTaskDetail(taskId);
  }

  activateView(link.dataset.viewLink);
});

document.addEventListener("change", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement || target instanceof HTMLSelectElement)) {
    return;
  }
  if (target.matches("[data-case-set-check]")) {
    const caseSetId = target.dataset.caseSetCheck || "";
    if (!caseSetId) {
      return;
    }
    if (target.checked) {
      selectedCaseSetIds.add(caseSetId);
    } else {
      selectedCaseSetIds.delete(caseSetId);
    }
    syncExportSelection();
  }
  if (target === scheduleTypeSelect) {
    syncScheduleTypeFields(target.value);
  }
  if (target === taskCaseSetSelect) {
    populateTaskMetricOptions(target.value);
  }
  if (target === metricTemplateSelect && metricModalMode === "create") {
    const templateMetricSet = getMetricSetById(target.value);
    if (metricFormScenario && templateMetricSet) {
      metricFormScenario.value = templateMetricSet.scenario_type;
    }
    if (metricFormDescription && templateMetricSet) {
      metricFormDescription.value = templateMetricSet.description;
    }
    if (metricFormThreshold && templateMetricSet) {
      metricFormThreshold.value = String(templateMetricSet.pass_threshold);
    }
    buildMetricEditRows(templateMetricSet?.dimensions || []);
  }
});

if (enterExportModeButton) {
  enterExportModeButton.addEventListener("click", () => {
    setExportMode(true);
  });
}

if (cancelExportButton) {
  cancelExportButton.addEventListener("click", () => {
    setExportMode(false);
  });
}

if (exportSelectedButton) {
  exportSelectedButton.addEventListener("click", async () => {
    if (selectedCaseSetIds.size === 0) {
      return;
    }
    exportSelectedButton.disabled = true;
    const originalText = exportSelectedButton.textContent;
    exportSelectedButton.textContent = "导出中...";
    try {
      for (const caseSetId of selectedCaseSetIds) {
        const card = document.querySelector(`.set-card[data-case-set-id="${caseSetId}"]`);
        const caseSetName = card?.dataset.caseSetName || caseSetId;
        await downloadCaseSet(caseSetId, `${caseSetName}.xlsx`);
      }
      setExportMode(false);
    } catch (error) {
      window.alert("导出失败，请稍后重试");
      syncExportSelection();
    } finally {
      exportSelectedButton.disabled = selectedCaseSetIds.size === 0;
      exportSelectedButton.textContent = originalText;
    }
  });
}

if (updateCaseSetButton && caseSetFileInput) {
  updateCaseSetButton.addEventListener("click", () => {
    caseSetFileInput.click();
  });
}

if (caseSetFileInput) {
  caseSetFileInput.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file || !currentCaseSetId || !updateCaseSetButton) {
      return;
    }
    updateCaseSetButton.disabled = true;
    const originalText = updateCaseSetButton.textContent;
    updateCaseSetButton.textContent = "更新中...";
    clearCaseSetFeedback();
    try {
      const detail = await importCaseSetFile(currentCaseSetId, file);
      renderCaseSetDetail(detail);
      showCaseSetFeedback(`已覆盖更新，共 ${detail.cases.length} 个用例`);
    } catch (error) {
      showCaseSetFeedback(error instanceof Error ? error.message : "更新失败，请稍后重试", true);
    } finally {
      updateCaseSetButton.disabled = false;
      updateCaseSetButton.textContent = originalText;
      caseSetFileInput.value = "";
    }
  });
}

if (exportCurrentCaseSetButton) {
  exportCurrentCaseSetButton.addEventListener("click", async () => {
    const currentName = currentCaseSetDetail?.case_set?.name || currentCaseSetId;
    exportCurrentCaseSetButton.disabled = true;
    const originalText = exportCurrentCaseSetButton.textContent;
    exportCurrentCaseSetButton.textContent = "导出中...";
    try {
      await downloadCaseSet(currentCaseSetId, `${currentName}.xlsx`);
    } catch (error) {
      showCaseSetFeedback("导出失败，请稍后重试", true);
    } finally {
      exportCurrentCaseSetButton.disabled = false;
      exportCurrentCaseSetButton.textContent = originalText;
    }
  });
}

metricFilterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentMetricFilter = button.dataset.metricFilter || "全部";
    metricFilterButtons.forEach((item) => item.classList.toggle("active", item === button));
    refreshMetricPage();
  });
});

if (openMetricModalButton) {
  openMetricModalButton.addEventListener("click", () => {
    openMetricModal("create");
  });
}

if (editMetricSetButton) {
  editMetricSetButton.addEventListener("click", () => {
    openMetricModal("edit");
  });
}

if (closeMetricModalButtons.length) {
  closeMetricModalButtons.forEach((button) => {
    button.addEventListener("click", closeMetricModal);
  });
}

if (metricForm) {
  metricForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const activeMetricSet = metricModalMode === "edit"
      ? getMetricSetById(currentMetricSetId)
      : getMetricSetById(metricTemplateSelect?.value || currentMetricSetId);
    const name = String(metricFormName?.value || "").trim();
    const scenarioType = String(metricFormScenario?.value || "").trim();
    const description = String(metricFormDescription?.value || "").trim();
    const passThreshold = Number.parseFloat(String(metricFormThreshold?.value || "").trim());

    if (!activeMetricSet || !name || !scenarioType || Number.isNaN(passThreshold)) {
      showMetricError("请填写所有必填项");
      return;
    }

    if (metricSubmitButton) {
      metricSubmitButton.disabled = true;
    }
    const originalText = metricSubmitButton?.textContent || "保存参数组合";
    if (metricSubmitButton) {
      metricSubmitButton.textContent = "保存中...";
    }

    try {
      const dimensions = readMetricDimensionsFromForm(activeMetricSet);
      if (metricModalMode === "edit") {
        await updateMetricSet(activeMetricSet.metric_set_id, {
          name,
          description,
          pass_threshold: passThreshold,
          dimensions,
        });
        currentMetricSetId = activeMetricSet.metric_set_id;
      } else {
        const response = await createMetricSet({
          name,
          scenario_type: scenarioType,
          description,
          score_formula: activeMetricSet.score_formula,
          pass_threshold: passThreshold,
          dimensions,
          benchmark_refs: activeMetricSet.benchmark_refs,
        });
        currentMetricSetId = response.metric_set.metric_set_id;
      }
      await loadMetricSets();
      await loadTasks();
      if (currentTaskId) {
        await loadTaskDetail(currentTaskId);
      }
      closeMetricModal();
      activateView("metric-sets");
    } catch (error) {
      showMetricError(error instanceof Error ? error.message : "保存失败，请稍后重试");
    } finally {
      if (metricSubmitButton) {
        metricSubmitButton.disabled = false;
        metricSubmitButton.textContent = originalText;
      }
    }
  });
}

if (openTaskModalButton) {
  openTaskModalButton.addEventListener("click", openTaskModal);
}

if (closeTaskModalButtons.length) {
  closeTaskModalButtons.forEach((button) => {
    button.addEventListener("click", closeTaskModal);
  });
}

if (taskForm) {
  taskForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitter = event.submitter;
    const launchMode = submitter?.dataset.launchMode;
    const formData = new FormData(taskForm);
    const name = String(formData.get("name") || "").trim();
    const caseSetId = String(formData.get("case_set_id") || "").trim();
    const environmentId = String(formData.get("environment_id") || "").trim();
    const metricSetId = String(formData.get("metric_set_id") || "").trim();
    const repeatCountValue = String(formData.get("repeat_count") || "").trim();
    const repeatCount = Number.parseInt(repeatCountValue, 10);

    if (!name || !caseSetId || !environmentId || !metricSetId || !repeatCount || !launchMode) {
      showTaskError("请填写所有必填项");
      return;
    }

    if (submitter) {
      submitter.disabled = true;
    }
    if (taskSubmit) {
      taskSubmit.disabled = true;
    }

    try {
      const payload = await createTask({
        name,
        case_set_id: caseSetId,
        environment_id: environmentId,
        metric_set_id: metricSetId,
        repeat_count: repeatCount,
        launch_mode: launchMode,
      });
      await loadTasks();
      await loadSchedules();
      if (launchMode === "immediate" && payload.task?.task_id) {
        currentTaskId = payload.task.task_id;
        await loadTaskDetail(currentTaskId);
      }
      activateView("runs");
      closeTaskModal();
    } catch (error) {
      showTaskError(error instanceof Error ? error.message : "创建失败，请稍后重试");
    } finally {
      if (submitter) {
        submitter.disabled = false;
      }
      if (taskSubmit) {
        taskSubmit.disabled = false;
      }
    }
  });
}

if (openScheduleModalButton) {
  openScheduleModalButton.addEventListener("click", openScheduleModal);
}

if (closeScheduleModalButtons.length) {
  closeScheduleModalButtons.forEach((button) => {
    button.addEventListener("click", closeScheduleModal);
  });
}

if (scheduleForm) {
  scheduleForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!scheduleSubmit) {
      return;
    }
    const formData = new FormData(scheduleForm);
    const name = String(formData.get("name") || "").trim();
    const taskId = String(formData.get("task_id") || "").trim();
    const scheduleType = String(formData.get("schedule_type") || "").trim();
    const runAt = String(formData.get("run_at") || "").trim();
    const dailyTime = String(formData.get("daily_time") || "").trim();
    const scheduleStatus = String(formData.get("schedule_status") || "").trim() || "enabled";

    if (!name || !taskId || !scheduleType || (scheduleType === "one_time" && !runAt) || (scheduleType === "daily" && !dailyTime)) {
      showScheduleError("请填写所有必填项");
      return;
    }

    scheduleSubmit.disabled = true;
    const originalText = scheduleSubmit.textContent;
    scheduleSubmit.textContent = "创建中...";
    try {
      await createSchedule({
        name,
        task_id: taskId,
        schedule_type: scheduleType,
        run_at: scheduleType === "one_time" ? runAt : null,
        daily_time: scheduleType === "daily" ? dailyTime : null,
        schedule_status: scheduleStatus,
      });
      await loadTasks();
      await loadSchedules();
      if (currentTaskId === taskId) {
        await loadTaskDetail(taskId);
      }
      activateView("schedules");
      closeScheduleModal();
    } catch (error) {
      showScheduleError(error instanceof Error ? error.message : "创建失败，请稍后重试");
    } finally {
      scheduleSubmit.disabled = false;
      scheduleSubmit.textContent = originalText;
    }
  });
}

if (executeTaskButton) {
  executeTaskButton.addEventListener("click", async () => {
    const taskId = executeTaskButton.dataset.taskId || currentTaskId;
    if (!taskId) {
      return;
    }
    executeTaskButton.disabled = true;
    const originalText = executeTaskButton.textContent;
    executeTaskButton.textContent = "执行中...";
    try {
      await executeTask(taskId);
      await loadTasks();
      await loadSchedules();
      await loadTaskDetail(taskId);
    } finally {
      executeTaskButton.disabled = false;
      executeTaskButton.textContent = originalText;
    }
  });
}

activateView("dashboard");
setExportMode(false);
syncScheduleTypeFields(scheduleTypeSelect?.value || "one_time");
void loadCaseSetDetail(currentCaseSetId);
void loadMetricSets();
void loadTasks();
void loadSchedules();
