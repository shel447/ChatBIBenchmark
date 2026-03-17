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

function activateView(target) {
  views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === target);
  });
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === target);
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
  activateView(link.dataset.viewLink);
});

activateView("dashboard");

function activateTypePanel(type) {
  typePanels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.typePanel === type);
  });
}

if (typeSelect) {
  activateTypePanel(typeSelect.value);
  typeSelect.addEventListener("change", (event) => {
    activateTypePanel(event.target.value);
  });
}

function openRunModal() {
  if (!runModal) {
    return;
  }
  runModal.classList.remove("hidden");
  if (runError) {
    runError.classList.add("hidden");
  }
}

function closeRunModal() {
  if (!runModal) {
    return;
  }
  runModal.classList.add("hidden");
  if (runError) {
    runError.classList.add("hidden");
    runError.textContent = "请填写所有必填项";
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
  runError.classList.remove("hidden");
}

function formatDateTime(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => {
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

async function createRun(payload) {
  const response = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("request_failed");
  }
  return response.json();
}

function insertRunRow(values) {
  if (!runTableBody) {
    return;
  }
  const row = document.createElement("tr");
  row.className = "row-link";
  row.dataset.viewLink = "run-detail";
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

if (openRunModalButton) {
  openRunModalButton.addEventListener("click", openRunModal);
}

if (closeRunModalButtons.length) {
  closeRunModalButtons.forEach((button) => {
    button.addEventListener("click", closeRunModal);
  });
}

if (runForm) {
  runForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!runSubmit) {
      return;
    }
    const formData = new FormData(runForm);
    const name = String(formData.get("name") || "").trim();
    const caseSetId = String(formData.get("case_set_id") || "").trim();
    const environmentId = String(formData.get("environment_id") || "").trim();
    const metricSetId = String(formData.get("metric_set_id") || "").trim();
    const repeatCountValue = String(formData.get("repeat_count") || "").trim();
    const repeatCount = Number.parseInt(repeatCountValue, 10);

    if (!name || !caseSetId || !environmentId || !metricSetId || !repeatCount) {
      showRunError("请填写所有必填项");
      return;
    }

    runSubmit.disabled = true;
    const originalText = runSubmit.textContent;
    runSubmit.textContent = "创建中...";

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
        endedAt: "-",
        progressText: "0 / 0",
        progressPercent: 0,
        accuracyText: "0%",
      });

      closeRunModal();
    } catch (error) {
      showRunError("创建失败，请稍后重试");
    } finally {
      runSubmit.disabled = false;
      runSubmit.textContent = originalText;
    }
  });
}
