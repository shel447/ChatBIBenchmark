# Report Metric Activation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make report multi-turn metric sets participate in real scoring, gating, persistence, and UI observability.

**Architecture:** Keep the existing raw report evaluator as the evidence layer, then add a report metric-set aggregation layer that maps raw values to supported dimensions and computes weighted score plus hard gates. Expose the aggregated result through report APIs, persist both raw and aggregated metrics, and surface execution status plus mapping details in metric management UI.

**Tech Stack:** FastAPI, SQLite, vanilla JS frontend, Python unittest.

---

### Task 1: Lock backend behavior with failing tests

**Files:**
- Create: `tests/test_report_metric_activation_api.py`
- Modify: `tests/test_metric_sets_api.py`
- Modify: `tests/test_frontend_routes.py`

**Step 1: Write failing API tests**

Add tests for:
- `POST /api/report/evaluate` with `metric_set_id=metric-report-dialogue` returns `raw_metrics`, `applied_metric_set`, and `aggregated_metrics`
- hard gate failure forces `passed=false`
- non-report `metric_set_id` returns `400`
- missing required ground truth for active dimensions returns `400`
- repeated `POST /api/report/runs` calls aggregate multiple case results instead of overwriting the last case
- `GET /api/report/runs` and `GET /api/report/runs/{run_id}` return run summary plus case details

**Step 2: Verify they fail**

Run: `python -m unittest tests/test_report_metric_activation_api.py -v`

**Step 3: Extend metric-set and frontend route tests**

Add failing assertions for:
- report metric set exposes execution status and mapping info
- unsupported custom dimension key for report metric set is rejected
- frontend contains execution-status wording and mapping section labels

**Step 4: Verify they fail**

Run:
- `python -m unittest tests/test_metric_sets_api.py -v`
- `python -m unittest tests/test_frontend_routes.py -v`

### Task 2: Implement backend metric execution and persistence

**Files:**
- Modify: `backend/core/evaluator.py`
- Create: `backend/core/report_metric_sets.py`
- Modify: `backend/core/usecases/metric_set_usecases.py`
- Modify: `backend/storage/sqlite_store.py`
- Modify: `backend/app.py`

**Step 1: Implement raw evaluator compatibility**

Update report evaluation to:
- support `template_name` / `selected_template_name` with id fallback
- emit `delivery.report_generated`

**Step 2: Implement report metric-set aggregation**

Add helpers to:
- validate supported report dimension keys
- resolve raw metric values for each supported key
- compute weighted score, target pass, hard-gate pass, threshold pass, and final `passed`
- build mapping metadata for metric-set detail responses

**Step 3: Implement API wiring**

Update:
- `POST /api/report/evaluate`
- `POST /api/report/runs`
- `GET /api/report/runs`
- `GET /api/report/runs/{run_id}`

Behavior:
- no `metric_set_id` keeps legacy raw-only output
- valid report metric set returns raw + aggregated
- non-report metric set returns `400`
- missing required ground truth for active dimensions returns `400`

**Step 4: Implement persistence updates**

Persist:
- case-level `{ raw_metrics, aggregated_metrics }`
- run-level `{ raw_summary, aggregated_summary, case_count }`
- query helpers for listing run cases and recomputing summaries across all stored cases in a run

**Step 5: Re-run tests**

Run:
- `python -m unittest tests/test_report_metric_activation_api.py -v`
- `python -m unittest tests/test_metric_sets_api.py -v`

### Task 3: Implement metric-management observability in UI

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

**Step 1: Render execution status**

Show:
- `已接入执行` for active report metric sets
- `仅配置` for planned metric sets

**Step 2: Render mapping detail**

In metric-set detail, show rows for:
- dimension name
- execution source
- formula
- hard gate
- target

**Step 3: Re-run frontend tests**

Run: `python -m unittest tests/test_frontend_routes.py -v`

### Task 4: Full verification

**Files:**
- No code changes expected

**Step 1: Run targeted suite**

Run:
- `python -m unittest tests/test_report_evaluator.py tests/test_report_metric_activation_api.py tests/test_metric_sets_api.py tests/test_frontend_routes.py -v`

**Step 2: Run broader regression**

Run:
- `python -m unittest tests/test_case_sets_api.py tests/test_runs_api.py tests/test_tasks_schedules_api.py -v`
- `node --check frontend/app.js`
- `git diff --check`

**Step 3: Commit**

```bash
git add backend frontend tests docs/plans
git commit -m "feat: activate report metric set scoring"
```
