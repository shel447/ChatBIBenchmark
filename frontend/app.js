const navButtons = document.querySelectorAll("[data-view-target]");
const views = document.querySelectorAll("[data-view]");
const typeSelect = document.querySelector("[data-case-type]");
const typePanels = document.querySelectorAll("[data-type-panel]");

const taskModal = document.getElementById("run-modal");
const taskForm = document.getElementById("run-form");
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
          <td>${escapeHtml(task.metric_set_id)}</td>
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
  const { task, latest_execution: latestExecution, execution_history: history, schedule } = detail;
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
    taskDetailMetricSet.textContent = task.metric_set_id;
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
void loadTasks();
void loadSchedules();
