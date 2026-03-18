const navButtons = document.querySelectorAll("[data-view-target]");
const views = document.querySelectorAll("[data-view]");
const typeSelect = document.querySelector("[data-case-type]");
const typePanels = document.querySelectorAll("[data-type-panel]");
const runModal = document.getElementById("run-modal");
const runForm = document.getElementById("run-form");
const openRunModalButton = document.querySelector("[data-open-run-modal]");
const closeRunModalButtons = document.querySelectorAll("[data-close-run-modal]");
const runError = document.querySelector("[data-run-error]");
const runSubmit = document.querySelector("[data-run-submit]");
const runTableBody = document.querySelector('[data-view="runs"] .table tbody');
const caseSetsView = document.querySelector('[data-view="case-sets"]');
const caseSetCards = document.querySelectorAll('.set-card[data-case-set-id]');
const defaultCaseSetActions = document.querySelector('[data-default-case-set-actions]');
const exportToolbar = document.querySelector('[data-export-toolbar]');
const exportCount = document.querySelector('[data-export-count]');
const enterExportModeButton = document.querySelector('[data-enter-export-mode]');
const exportSelectedButton = document.querySelector('[data-export-selected]');
const cancelExportButton = document.querySelector('[data-cancel-export]');
const caseSetHeading = document.querySelector('[data-case-set-heading]');
const caseSetTypeChip = document.querySelector('[data-case-set-type-chip]');
const caseSetCountChip = document.querySelector('[data-case-set-count-chip]');
const caseSetStatusChip = document.querySelector('[data-case-set-status-chip]');
const caseSetFeedback = document.querySelector('[data-case-set-feedback]');
const caseListBody = document.querySelector('[data-case-list-body]');
const updateCaseSetButton = document.querySelector('[data-update-case-set]');
const exportCurrentCaseSetButton = document.querySelector('[data-export-current-case-set]');
const caseSetFileInput = document.querySelector('[data-case-set-file-input]');

const difficultyLabels = ['低', '中', '高'];

let currentCaseSetId = 'cs-nl2sql';
let currentCaseSetDetail = null;
let exportMode = false;
const selectedCaseSetIds = new Set();

function activateView(target) {
  views.forEach((view) => {
    view.classList.toggle('active', view.dataset.view === target);
  });
  navButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.viewTarget === target);
  });
  if (target !== 'case-sets') {
    setExportMode(false);
  }
}

function activateTypePanel(type) {
  typePanels.forEach((panel) => {
    panel.classList.toggle('active', panel.dataset.typePanel === type);
  });
}

function formatDateTime(date) {
  const pad = (value) => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };
    return map[char];
  });
}

function openRunModal() {
  if (!runModal) {
    return;
  }
  runModal.classList.remove('hidden');
  if (runError) {
    runError.classList.add('hidden');
  }
}

function closeRunModal() {
  if (!runModal) {
    return;
  }
  runModal.classList.add('hidden');
  if (runError) {
    runError.classList.add('hidden');
    runError.textContent = '请填写所有必填项';
  }
  if (runForm) {
    runForm.reset();
  }
}

function showRunError(message) {
  if (!runError) {
    return;
  }
  runError.textContent = message;
  runError.classList.remove('hidden');
}

function showCaseSetFeedback(message, isError = false) {
  if (!caseSetFeedback) {
    return;
  }
  caseSetFeedback.textContent = message;
  caseSetFeedback.classList.remove('hidden');
  caseSetFeedback.classList.toggle('error', isError);
}

function clearCaseSetFeedback() {
  if (!caseSetFeedback) {
    return;
  }
  caseSetFeedback.classList.add('hidden');
  caseSetFeedback.classList.remove('error');
  caseSetFeedback.textContent = '';
}

function syncExportSelection() {
  caseSetCards.forEach((card) => {
    const caseSetId = card.dataset.caseSetId;
    const isSelected = selectedCaseSetIds.has(caseSetId);
    card.classList.toggle('selected', isSelected);
    const checkbox = card.querySelector('[data-case-set-check]');
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
    caseSetsView.classList.toggle('export-mode', enabled);
  }
  if (defaultCaseSetActions) {
    defaultCaseSetActions.classList.toggle('hidden', enabled);
  }
  if (exportToolbar) {
    exportToolbar.classList.toggle('hidden', !enabled);
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

async function downloadCaseSet(caseSetId, fallbackName) {
  const response = await fetch(`/api/case-sets/${encodeURIComponent(caseSetId)}/export`);
  if (!response.ok) {
    throw new Error('download_failed');
  }
  const blob = await response.blob();
  const filename = parseFilename(response.headers.get('content-disposition'), fallbackName);
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 0);
}

async function createRun(payload) {
  const response = await fetch('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('request_failed');
  }
  return response.json();
}

async function fetchCaseSetDetail(caseSetId) {
  const response = await fetch(`/api/case-sets/${encodeURIComponent(caseSetId)}`);
  if (!response.ok) {
    throw new Error('request_failed');
  }
  return response.json();
}

async function importCaseSetFile(caseSetId, file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`/api/case-sets/${encodeURIComponent(caseSetId)}/import`, {
    method: 'POST',
    body: formData,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || '导入失败');
  }
  return payload;
}

function insertRunRow(values) {
  if (!runTableBody) {
    return;
  }
  const row = document.createElement('tr');
  row.className = 'row-link';
  row.dataset.viewLink = 'run-detail';
  row.innerHTML = `
    <td>${escapeHtml(values.name)}</td>
    <td>${escapeHtml(values.caseSetLabel)}</td>
    <td>${escapeHtml(values.environmentLabel)}</td>
    <td>${escapeHtml(values.startedAt)}</td>
    <td>${escapeHtml(values.endedAt)}</td>
    <td>${escapeHtml(values.metricLabel)}</td>
    <td>
      <div class="progress-cell">
        <span class="progress-text">${escapeHtml(values.progressText)}</span>
        <div class="progress-bar" aria-label="进度条">
          <div class="progress-fill" style="width: ${values.progressPercent}%"></div>
        </div>
      </div>
    </td>
    <td class="strong">${escapeHtml(values.accuracyText)}</td>
  `;
  runTableBody.prepend(row);
}

function buildCaseRow(caseItem, index, isSeed) {
  const difficulty = difficultyLabels[index % difficultyLabels.length];
  const status = isSeed ? '不可评测' : '待评测';
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
  const meta = card.querySelector('.set-meta');
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
    caseSetStatusChip.textContent = caseSet.is_seed ? '种子，不可评测' : '可导出，可评测';
  }
  if (caseListBody) {
    if (cases.length === 0) {
      caseListBody.innerHTML = `
        <tr>
          <td colspan="5">当前用例集暂无用例</td>
        </tr>
      `;
    } else {
      caseListBody.innerHTML = cases.map((caseItem, index) => buildCaseRow(caseItem, index, caseSet.is_seed)).join('');
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
      showCaseSetFeedback('加载用例集失败，请稍后重试', true);
    }
    return null;
  }
}

if (typeSelect) {
  activateTypePanel(typeSelect.value);
  typeSelect.addEventListener('change', (event) => {
    activateTypePanel(event.target.value);
  });
}

navButtons.forEach((button) => {
  button.addEventListener('click', () => {
    activateView(button.dataset.viewTarget);
  });
});

document.addEventListener('click', (event) => {
  const link = event.target.closest('[data-view-link]');
  if (!link) {
    return;
  }

  if (link.classList.contains('set-card')) {
    if (exportMode) {
      if (!event.target.closest('.set-select')) {
        toggleCaseSetSelection(link.dataset.caseSetId || '');
      }
      return;
    }
    const caseSetId = link.dataset.caseSetId;
    if (caseSetId) {
      currentCaseSetId = caseSetId;
      void loadCaseSetDetail(caseSetId);
    }
  }

  activateView(link.dataset.viewLink);
});

document.addEventListener('change', (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) {
    return;
  }
  if (target.matches('[data-case-set-check]')) {
    const caseSetId = target.dataset.caseSetCheck || '';
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
});

if (enterExportModeButton) {
  enterExportModeButton.addEventListener('click', () => {
    setExportMode(true);
  });
}

if (cancelExportButton) {
  cancelExportButton.addEventListener('click', () => {
    setExportMode(false);
  });
}

if (exportSelectedButton) {
  exportSelectedButton.addEventListener('click', async () => {
    if (selectedCaseSetIds.size === 0) {
      return;
    }
    exportSelectedButton.disabled = true;
    const originalText = exportSelectedButton.textContent;
    exportSelectedButton.textContent = '导出中...';
    try {
      for (const caseSetId of selectedCaseSetIds) {
        const card = document.querySelector(`.set-card[data-case-set-id="${caseSetId}"]`);
        const caseSetName = card?.dataset.caseSetName || caseSetId;
        await downloadCaseSet(caseSetId, `${caseSetName}.xlsx`);
      }
      setExportMode(false);
    } catch (error) {
      window.alert('导出失败，请稍后重试');
      syncExportSelection();
    } finally {
      exportSelectedButton.disabled = selectedCaseSetIds.size === 0;
      exportSelectedButton.textContent = originalText;
    }
  });
}

if (updateCaseSetButton && caseSetFileInput) {
  updateCaseSetButton.addEventListener('click', () => {
    caseSetFileInput.click();
  });
}

if (caseSetFileInput) {
  caseSetFileInput.addEventListener('change', async (event) => {
    const file = event.target.files?.[0];
    if (!file || !currentCaseSetId || !updateCaseSetButton) {
      return;
    }
    updateCaseSetButton.disabled = true;
    const originalText = updateCaseSetButton.textContent;
    updateCaseSetButton.textContent = '更新中...';
    clearCaseSetFeedback();
    try {
      const detail = await importCaseSetFile(currentCaseSetId, file);
      renderCaseSetDetail(detail);
      showCaseSetFeedback(`已覆盖更新，共 ${detail.cases.length} 个用例`);
    } catch (error) {
      showCaseSetFeedback(error instanceof Error ? error.message : '更新失败，请稍后重试', true);
    } finally {
      updateCaseSetButton.disabled = false;
      updateCaseSetButton.textContent = originalText;
      caseSetFileInput.value = '';
    }
  });
}

if (exportCurrentCaseSetButton) {
  exportCurrentCaseSetButton.addEventListener('click', async () => {
    const currentName = currentCaseSetDetail?.case_set?.name || currentCaseSetId;
    exportCurrentCaseSetButton.disabled = true;
    const originalText = exportCurrentCaseSetButton.textContent;
    exportCurrentCaseSetButton.textContent = '导出中...';
    try {
      await downloadCaseSet(currentCaseSetId, `${currentName}.xlsx`);
    } catch (error) {
      showCaseSetFeedback('导出失败，请稍后重试', true);
    } finally {
      exportCurrentCaseSetButton.disabled = false;
      exportCurrentCaseSetButton.textContent = originalText;
    }
  });
}

if (openRunModalButton) {
  openRunModalButton.addEventListener('click', openRunModal);
}

if (closeRunModalButtons.length) {
  closeRunModalButtons.forEach((button) => {
    button.addEventListener('click', closeRunModal);
  });
}

if (runForm) {
  runForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!runSubmit) {
      return;
    }
    const formData = new FormData(runForm);
    const name = String(formData.get('name') || '').trim();
    const caseSetId = String(formData.get('case_set_id') || '').trim();
    const environmentId = String(formData.get('environment_id') || '').trim();
    const metricSetId = String(formData.get('metric_set_id') || '').trim();
    const repeatCountValue = String(formData.get('repeat_count') || '').trim();
    const repeatCount = Number.parseInt(repeatCountValue, 10);

    if (!name || !caseSetId || !environmentId || !metricSetId || !repeatCount) {
      showRunError('请填写所有必填项');
      return;
    }

    runSubmit.disabled = true;
    const originalText = runSubmit.textContent;
    runSubmit.textContent = '创建中...';

    try {
      await createRun({
        name,
        case_set_id: caseSetId,
        environment_id: environmentId,
        metric_set_id: metricSetId,
        repeat_count: repeatCount,
      });

      const caseSetLabel = runForm.querySelector('select[name="case_set_id"] option:checked')?.textContent || caseSetId;
      const environmentLabel = runForm.querySelector('select[name="environment_id"] option:checked')?.textContent || environmentId;
      const metricLabel = runForm.querySelector('select[name="metric_set_id"] option:checked')?.textContent || metricSetId;
      const now = formatDateTime(new Date());

      insertRunRow({
        name,
        caseSetLabel,
        environmentLabel,
        metricLabel,
        startedAt: now,
        endedAt: '-',
        progressText: '0 / 0',
        progressPercent: 0,
        accuracyText: '0%',
      });

      closeRunModal();
    } catch (error) {
      showRunError('创建失败，请稍后重试');
    } finally {
      runSubmit.disabled = false;
      runSubmit.textContent = originalText;
    }
  });
}

activateView('dashboard');
setExportMode(false);
void loadCaseSetDetail(currentCaseSetId);
