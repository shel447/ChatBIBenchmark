import json
import os
import threading
from time import sleep

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from .adapters.sqlite_adapter import SQLiteAdapter
from .core.evaluator import evaluate_report_case
from .core.report_metric_sets import (
    ACTIVE_SCENARIO_TYPE,
    aggregate_report_metric_set,
    summarize_report_run,
    validate_report_case_requirements,
)
from .core.usecases.case_set_usecases import export_case_set, get_case_set_detail, import_case_set, list_case_sets
from .core.usecases.execution_result_usecases import materialize_execution_results
from .core.usecases.metric_set_usecases import create_metric_set, get_metric_set, list_metric_sets, update_metric_set
from .core.usecases.run_usecases import get_run as get_execution_run, list_runs as list_execution_runs
from .core.usecases.task_report_usecases import build_task_report_bundle, export_task_report, list_task_report_profiles
from .core.usecases.trend_usecases import get_case_set_trends, get_case_trends, get_overview_analytics
from .core.usecases.schedule_usecases import (
    DEFAULT_TIMEZONE,
    create_schedule,
    delete_schedule,
    get_schedule,
    list_schedules,
    process_due_schedules,
    update_schedule,
)
from .core.usecases.task_usecases import create_task, execute_task, get_task, list_task_executions, list_tasks
from .storage.case_set_repository import SqliteCaseSetRepository, init_case_set_db
from .storage.run_repository import (
    SqliteMetricSetRepository,
    SqliteRunRepository,
    SqliteScheduleRepository,
    SqliteTaskRepository,
    init_run_db,
)
from .storage.sqlite_store import (
    get_run as get_report_run,
    init_db,
    list_case_results as list_report_case_results,
    list_runs as list_report_runs,
    save_case_result,
    save_run,
)

APP_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "frontend"))
DATA_DIR = os.path.join(APP_DIR, "data")
DEFAULT_META_DB = os.path.join(APP_DIR, "report_eval.db")
DEFAULT_RUN_DB = os.path.join(APP_DIR, "runs.db")
DEFAULT_CASE_SET_DB = os.path.join(APP_DIR, "case_sets.db")
SCHEDULER_INTERVAL_SECONDS = 30

app = FastAPI(title="ChatBI Report Eval")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _task_to_dict(task):
    return {
        "task_id": task.task_id,
        "name": task.name,
        "case_set_id": task.case_set_id,
        "environment_id": task.environment_id,
        "metric_set_id": task.metric_set_id,
        "repeat_count": task.repeat_count,
        "launch_mode": task.launch_mode,
        "task_status": task.task_status,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "latest_execution_id": task.latest_execution_id,
    }


def _metric_set_to_dict(metric_set):
    return {
        "metric_set_id": metric_set.metric_set_id,
        "name": metric_set.name,
        "scenario_type": metric_set.scenario_type,
        "description": metric_set.description,
        "score_formula": metric_set.score_formula,
        "pass_threshold": metric_set.pass_threshold,
        "dimensions": metric_set.dimensions,
        "benchmark_refs": metric_set.benchmark_refs,
        "created_at": metric_set.created_at,
        "updated_at": metric_set.updated_at,
    }


def _run_to_dict(run):
    return {
        "run_id": run.run_id,
        "task_id": run.task_id,
        "name": run.name,
        "case_set_id": run.case_set_id,
        "environment_id": run.environment_id,
        "metric_set_id": run.metric_set_id,
        "repeat_count": run.repeat_count,
        "total_cases": run.total_cases,
        "executed_cases": run.executed_cases,
        "accuracy": run.accuracy,
        "trigger_source": run.trigger_source,
        "execution_status": run.execution_status,
        "started_at": run.started_at,
        "ended_at": run.ended_at,
    }


def _case_result_to_dict(item):
    return {
        "run_id": item.run_id,
        "task_id": item.task_id,
        "case_set_id": item.case_set_id,
        "case_id": item.case_id,
        "case_title": item.case_title,
        "case_type": item.case_type,
        "accuracy": item.accuracy,
        "status": item.status,
        "issue_tags": item.issue_tags,
        "detail_metrics": item.detail_metrics,
        "summary": item.summary,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _schedule_to_dict(schedule):
    return {
        "schedule_id": schedule.schedule_id,
        "name": schedule.name,
        "task_id": schedule.task_id,
        "schedule_type": schedule.schedule_type,
        "run_at": schedule.run_at,
        "daily_time": schedule.daily_time,
        "timezone": schedule.timezone,
        "schedule_status": schedule.schedule_status,
        "last_triggered_at": schedule.last_triggered_at,
        "next_triggered_at": schedule.next_triggered_at,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
    }


def _get_schedule_summary_for_task(task_id: str):
    schedule_repo = SqliteScheduleRepository(DEFAULT_RUN_DB)
    active = schedule_repo.get_active_for_task(task_id)
    if active:
        return _schedule_to_dict(active)
    for schedule in schedule_repo.list():
        if schedule.task_id == task_id:
            return _schedule_to_dict(schedule)
    return None


def _get_metric_set_summary(metric_set_id: str):
    metric_repo = SqliteMetricSetRepository(DEFAULT_RUN_DB)
    metric_set = metric_repo.get(metric_set_id)
    if not metric_set:
        return None
    return {
        "metric_set_id": metric_set.metric_set_id,
        "name": metric_set.name,
        "scenario_type": metric_set.scenario_type,
    }


def _build_task_payload(task):
    run_repo = SqliteRunRepository(DEFAULT_RUN_DB)
    latest_execution = run_repo.get(task.latest_execution_id) if task.latest_execution_id else None
    return {
        **_task_to_dict(task),
        "metric_set": _get_metric_set_summary(task.metric_set_id),
        "latest_execution": _run_to_dict(latest_execution) if latest_execution else None,
        "schedule": _get_schedule_summary_for_task(task.task_id),
    }


def _require_metric_set(metric_set_id: str):
    metric_repo = SqliteMetricSetRepository(DEFAULT_RUN_DB)
    metric_set = metric_repo.get(metric_set_id)
    if not metric_set:
        raise HTTPException(status_code=400, detail="metric_set not found")
    return metric_set


def _require_report_metric_set(metric_set_id: str):
    metric_set = _require_metric_set(metric_set_id)
    if metric_set.scenario_type != ACTIVE_SCENARIO_TYPE:
        raise HTTPException(status_code=400, detail="metric_set must target 报告多轮交互")
    return metric_set


def _report_metric_set_summary(metric_set):
    if not metric_set:
        return None
    return {
        "metric_set_id": metric_set.metric_set_id,
        "name": metric_set.name,
        "scenario_type": metric_set.scenario_type,
    }


def _normalize_report_case_result(row):
    metrics = row.get("metrics") or {}
    raw_metrics = metrics.get("raw_metrics")
    aggregated_metrics = metrics.get("aggregated_metrics")
    if raw_metrics is None:
        raw_metrics = metrics
    return {
        "case_id": row.get("case_id"),
        "raw_metrics": raw_metrics or {},
        "aggregated_metrics": aggregated_metrics,
        "details": row.get("details") or {},
    }


def _serialize_report_run_row(run_row):
    config = run_row.get("config") or {}
    metric_set_id = config.get("metric_set_id")
    metric_set = SqliteMetricSetRepository(DEFAULT_RUN_DB).get(metric_set_id) if metric_set_id else None
    return {
        "run_id": run_row.get("run_id"),
        "created_at": run_row.get("created_at"),
        "config": config,
        "metrics": run_row.get("metrics") or {},
        "metric_set": _report_metric_set_summary(metric_set),
    }


def _evaluate_report_with_metric_set(case_payload, output_payload, config, data_db_path, metric_set_id=None):
    adapter = SQLiteAdapter(data_db_path)
    raw_metrics = evaluate_report_case(case_payload, output_payload, adapter, config)
    metric_set = None
    aggregated_metrics = None
    if metric_set_id:
        metric_set = _require_report_metric_set(metric_set_id)
        validate_report_case_requirements(metric_set, case_payload)
        aggregated_metrics = aggregate_report_metric_set(metric_set, raw_metrics, config)
    return raw_metrics, metric_set, aggregated_metrics


def _scheduler_loop(stop_event: threading.Event):
    while not stop_event.is_set():
        process_due_schedules(DEFAULT_RUN_DB, DEFAULT_CASE_SET_DB)
        stop_event.wait(SCHEDULER_INTERVAL_SECONDS)


@app.on_event("startup")
async def _startup():
    init_db(DEFAULT_META_DB)
    init_run_db(DEFAULT_RUN_DB)
    init_case_set_db(DEFAULT_CASE_SET_DB)
    stop_event = threading.Event()
    scheduler_thread = threading.Thread(target=_scheduler_loop, args=(stop_event,), daemon=True)
    app.state.scheduler_stop_event = stop_event
    app.state.scheduler_thread = scheduler_thread
    scheduler_thread.start()


@app.on_event("shutdown")
async def _shutdown():
    stop_event = getattr(app.state, "scheduler_stop_event", None)
    scheduler_thread = getattr(app.state, "scheduler_thread", None)
    if stop_event:
        stop_event.set()
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=1)


@app.get("/")
async def root():
    return RedirectResponse(url="/frontend/")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/report/templates")
async def list_templates():
    path = os.path.join(DATA_DIR, "report_templates.sample.json")
    return _load_json(path)


@app.get("/api/report/cases")
async def list_cases():
    path = os.path.join(DATA_DIR, "report_cases.sample.json")
    return _load_json(path)


@app.get("/api/case-sets")
async def list_case_sets_api():
    repo = SqliteCaseSetRepository(DEFAULT_CASE_SET_DB)
    return {"case_sets": list_case_sets(repo)}


@app.get("/api/case-sets/{case_set_id}")
async def get_case_set_api(case_set_id: str):
    repo = SqliteCaseSetRepository(DEFAULT_CASE_SET_DB)
    detail = get_case_set_detail(repo, case_set_id)
    if not detail:
        raise HTTPException(status_code=404, detail="case_set not found")
    return detail


@app.get("/api/case-sets/{case_set_id}/export")
async def export_case_set_api(case_set_id: str):
    repo = SqliteCaseSetRepository(DEFAULT_CASE_SET_DB)
    result = export_case_set(repo, case_set_id)
    if not result:
        raise HTTPException(status_code=404, detail="case_set not found")
    _, content = result
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{case_set_id}.xlsx"'},
    )


@app.post("/api/case-sets/{case_set_id}/import")
async def import_case_set_api(case_set_id: str, file: UploadFile = File(...)):
    repo = SqliteCaseSetRepository(DEFAULT_CASE_SET_DB)
    try:
        content = await file.read()
        detail = import_case_set(repo, case_set_id, content)
        if not detail:
            raise HTTPException(status_code=404, detail="case_set not found")
        return detail
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/metric-sets")
async def list_metric_sets_api():
    repo = SqliteMetricSetRepository(DEFAULT_RUN_DB)
    return {"metric_sets": list_metric_sets(repo)}


@app.get("/api/metric-sets/{metric_set_id}")
async def get_metric_set_api(metric_set_id: str):
    repo = SqliteMetricSetRepository(DEFAULT_RUN_DB)
    metric_set = get_metric_set(repo, metric_set_id)
    if not metric_set:
        raise HTTPException(status_code=404, detail="metric_set not found")
    return {"metric_set": metric_set}


@app.post("/api/metric-sets")
async def create_metric_set_api(request: Request):
    payload = await request.json()
    repo = SqliteMetricSetRepository(DEFAULT_RUN_DB)
    try:
        metric_set = create_metric_set(
            repo,
            payload["name"],
            payload["scenario_type"],
            payload["description"],
            payload.get("score_formula", "weighted_sum_with_gates"),
            payload["pass_threshold"],
            payload["dimensions"],
            payload.get("benchmark_refs", []),
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"{exc.args[0]} is required") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"metric_set": metric_set}


@app.patch("/api/metric-sets/{metric_set_id}")
async def update_metric_set_api(metric_set_id: str, request: Request):
    payload = await request.json()
    repo = SqliteMetricSetRepository(DEFAULT_RUN_DB)
    try:
        metric_set = update_metric_set(
            repo,
            metric_set_id,
            name=payload.get("name"),
            description=payload.get("description"),
            pass_threshold=payload.get("pass_threshold"),
            dimensions=payload.get("dimensions"),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"metric_set": metric_set}


@app.post("/api/tasks")
async def create_task_api(request: Request):
    payload = await request.json()
    required_fields = ("name", "case_set_id", "environment_id", "metric_set_id", "repeat_count", "launch_mode")
    for field in required_fields:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"{field} is required")
    _require_metric_set(payload["metric_set_id"])

    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    run_repo = SqliteRunRepository(DEFAULT_RUN_DB)
    case_set_repo = SqliteCaseSetRepository(DEFAULT_CASE_SET_DB)
    try:
        task, latest_execution = create_task(
            task_repo,
            run_repo,
            payload["name"],
            payload["case_set_id"],
            payload["environment_id"],
            payload["metric_set_id"],
            payload["repeat_count"],
            payload["launch_mode"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    latest_case_results = []
    if latest_execution:
        materialized = materialize_execution_results(run_repo, task_repo, case_set_repo, latest_execution.run_id)
        latest_execution = materialized["run"] if materialized else latest_execution
        latest_case_results = [_case_result_to_dict(item) for item in (materialized["case_results"] if materialized else [])]
        task = task_repo.get(task.task_id) or task

    response = {"task": _task_to_dict(task), "metric_set": _get_metric_set_summary(task.metric_set_id)}
    if latest_execution:
        response["latest_execution"] = _run_to_dict(latest_execution)
        response["latest_case_results"] = latest_case_results
    return response

@app.get("/api/tasks")
async def list_tasks_api():
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    return {"tasks": [_build_task_payload(task) for task in list_tasks(task_repo)]}


@app.get("/api/tasks/{task_id}")
async def get_task_api(task_id: str):
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    run_repo = SqliteRunRepository(DEFAULT_RUN_DB)
    task = get_task(task_repo, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    latest_execution = run_repo.get(task.latest_execution_id) if task.latest_execution_id else None
    latest_case_results = run_repo.list_case_results(task.latest_execution_id) if task.latest_execution_id else []
    return {
        "task": _task_to_dict(task),
        "metric_set": _get_metric_set_summary(task.metric_set_id),
        "schedule": _get_schedule_summary_for_task(task_id),
        "latest_execution": _run_to_dict(latest_execution) if latest_execution else None,
        "latest_case_results": [_case_result_to_dict(item) for item in latest_case_results],
        "execution_history": [_run_to_dict(run) for run in list_task_executions(run_repo, task_id)],
    }


@app.get("/api/task-report-profiles")
async def list_task_report_profiles_api():
    return {"profiles": list_task_report_profiles()}


@app.post("/api/tasks/{task_id}/export")
async def export_task_report_api(task_id: str, request: Request):
    payload = await request.json()
    profile_id = payload.get("profile_id")
    if not profile_id:
        raise HTTPException(status_code=400, detail="profile_id is required")
    bundle = build_task_report_bundle(
        SqliteTaskRepository(DEFAULT_RUN_DB),
        SqliteRunRepository(DEFAULT_RUN_DB),
        SqliteCaseSetRepository(DEFAULT_CASE_SET_DB),
        SqliteMetricSetRepository(DEFAULT_RUN_DB),
        SqliteScheduleRepository(DEFAULT_RUN_DB),
        task_id,
        payload.get("run_id"),
    )
    if not bundle:
        raise HTTPException(status_code=404, detail="task not found")
    if not bundle["latest_execution"]:
        raise HTTPException(status_code=400, detail="task has no execution result")
    try:
        profile, content, media_type = export_task_report(profile_id, bundle)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    filename = f"task-report-{bundle['task'].task_id}{profile['file_extension']}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/case-sets/{case_set_id}/trends")
async def get_case_set_trends_api(case_set_id: str):
    detail = get_case_set_trends(SqliteCaseSetRepository(DEFAULT_CASE_SET_DB), SqliteRunRepository(DEFAULT_RUN_DB), case_set_id)
    if not detail:
        raise HTTPException(status_code=404, detail="case_set not found")
    return detail


@app.get("/api/case-sets/{case_set_id}/cases/{case_id}/trends")
async def get_case_trends_api(case_set_id: str, case_id: str):
    detail = get_case_trends(SqliteCaseSetRepository(DEFAULT_CASE_SET_DB), SqliteRunRepository(DEFAULT_RUN_DB), case_set_id, case_id)
    if not detail:
        raise HTTPException(status_code=404, detail="case trend not found")
    return detail


@app.get("/api/analytics/overview")
async def get_overview_analytics_api():
    return get_overview_analytics(SqliteCaseSetRepository(DEFAULT_CASE_SET_DB), SqliteRunRepository(DEFAULT_RUN_DB))


@app.post("/api/tasks/{task_id}/execute")
async def execute_task_api(task_id: str):
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    run_repo = SqliteRunRepository(DEFAULT_RUN_DB)
    case_set_repo = SqliteCaseSetRepository(DEFAULT_CASE_SET_DB)
    try:
        task, run = execute_task(task_repo, run_repo, task_id, trigger_source="manual")
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    materialized = materialize_execution_results(run_repo, task_repo, case_set_repo, run.run_id)
    task = task_repo.get(task.task_id) or task
    run = materialized["run"] if materialized else run
    case_results = [_case_result_to_dict(item) for item in (materialized["case_results"] if materialized else [])]
    return {"task": _task_to_dict(task), "metric_set": _get_metric_set_summary(task.metric_set_id), "run": _run_to_dict(run), "case_results": case_results}

@app.post("/api/runs")
async def create_run_api(request: Request):
    payload = await request.json()
    required_fields = ("name", "case_set_id", "environment_id", "metric_set_id", "repeat_count")
    for field in required_fields:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"{field} is required")
    _require_metric_set(payload["metric_set_id"])

    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    run_repo = SqliteRunRepository(DEFAULT_RUN_DB)
    case_set_repo = SqliteCaseSetRepository(DEFAULT_CASE_SET_DB)
    task, run = create_task(
        task_repo,
        run_repo,
        payload["name"],
        payload["case_set_id"],
        payload["environment_id"],
        payload["metric_set_id"],
        payload["repeat_count"],
        "immediate",
    )
    materialized = materialize_execution_results(run_repo, task_repo, case_set_repo, run.run_id)
    task = task_repo.get(task.task_id) or task
    run = materialized["run"] if materialized else run
    return {"task": _task_to_dict(task), "run": _run_to_dict(run), "case_results": [_case_result_to_dict(item) for item in (materialized["case_results"] if materialized else [])]}

@app.get("/api/runs")
async def list_runs_api():
    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    runs = [_run_to_dict(run) for run in list_execution_runs(repo)]
    return {"runs": runs}


@app.get("/api/runs/{run_id}")
async def get_run_api(run_id: str):
    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    run = get_execution_run(repo, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run": _run_to_dict(run), "case_results": [_case_result_to_dict(item) for item in repo.list_case_results(run_id)]}

@app.post("/api/schedules")
async def create_schedule_api(request: Request):
    payload = await request.json()
    required_fields = ("name", "task_id", "schedule_type")
    for field in required_fields:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"{field} is required")
    schedule_status = payload.get("schedule_status", "enabled")
    schedule_repo = SqliteScheduleRepository(DEFAULT_RUN_DB)
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    try:
        schedule = create_schedule(
            schedule_repo,
            task_repo,
            payload["name"],
            payload["task_id"],
            payload["schedule_type"],
            payload.get("run_at"),
            payload.get("daily_time"),
            schedule_status,
            payload.get("timezone", DEFAULT_TIMEZONE),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"schedule": _schedule_to_dict(schedule)}


@app.get("/api/schedules")
async def list_schedules_api():
    schedule_repo = SqliteScheduleRepository(DEFAULT_RUN_DB)
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    schedules = []
    for schedule in list_schedules(schedule_repo):
        task = task_repo.get(schedule.task_id)
        schedules.append(
            {
                **_schedule_to_dict(schedule),
                "task": {"task_id": task.task_id, "name": task.name} if task else None,
            }
        )
    return {"schedules": schedules}


@app.get("/api/schedules/{schedule_id}")
async def get_schedule_api(schedule_id: str):
    schedule_repo = SqliteScheduleRepository(DEFAULT_RUN_DB)
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    schedule = get_schedule(schedule_repo, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="schedule not found")
    task = task_repo.get(schedule.task_id)
    return {"schedule": _schedule_to_dict(schedule), "task": _task_to_dict(task) if task else None}


@app.patch("/api/schedules/{schedule_id}")
async def update_schedule_api(schedule_id: str, request: Request):
    payload = await request.json()
    schedule_repo = SqliteScheduleRepository(DEFAULT_RUN_DB)
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    try:
        schedule = update_schedule(
            schedule_repo,
            task_repo,
            schedule_id,
            schedule_status=payload.get("schedule_status"),
            run_at=payload.get("run_at"),
            daily_time=payload.get("daily_time"),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"schedule": _schedule_to_dict(schedule)}


@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule_api(schedule_id: str):
    schedule_repo = SqliteScheduleRepository(DEFAULT_RUN_DB)
    task_repo = SqliteTaskRepository(DEFAULT_RUN_DB)
    delete_schedule(schedule_repo, task_repo, schedule_id)
    return {"ok": True}


@app.post("/api/report/evaluate")
async def evaluate_case(request: Request):
    payload = await request.json()
    case_payload = payload.get("case")
    output_payload = payload.get("output")
    config = payload.get("config") or {}
    data_db_path = payload.get("data_db_path")
    metric_set_id = payload.get("metric_set_id")

    if not case_payload or not output_payload:
        raise HTTPException(status_code=400, detail="case and output are required")
    if not data_db_path:
        raise HTTPException(status_code=400, detail="data_db_path is required")

    try:
        raw_metrics, metric_set, aggregated_metrics = _evaluate_report_with_metric_set(
            case_payload,
            output_payload,
            config,
            data_db_path,
            metric_set_id=metric_set_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not metric_set:
        return {"metrics": raw_metrics}
    return {
        "raw_metrics": raw_metrics,
        "applied_metric_set": _report_metric_set_summary(metric_set),
        "aggregated_metrics": aggregated_metrics,
    }


@app.get("/api/report/runs")
async def list_report_runs_api():
    runs = [_serialize_report_run_row(row) for row in list_report_runs(DEFAULT_META_DB)]
    return {"runs": runs}


@app.get("/api/report/runs/{run_id}")
async def get_report_run_api(run_id: str):
    run_row = get_report_run(DEFAULT_META_DB, run_id)
    if not run_row:
        raise HTTPException(status_code=404, detail="report run not found")
    case_rows = [_normalize_report_case_result(item) for item in list_report_case_results(DEFAULT_META_DB, run_id)]
    metric_set_id = (run_row.get("config") or {}).get("metric_set_id")
    metric_set = SqliteMetricSetRepository(DEFAULT_RUN_DB).get(metric_set_id) if metric_set_id else None
    return {
        "run": _serialize_report_run_row(run_row),
        "metric_set": _report_metric_set_summary(metric_set),
        "case_results": case_rows,
    }


@app.post("/api/report/runs")
async def evaluate_and_store_run(request: Request):
    payload = await request.json()
    run_id = payload.get("run_id")
    case_payload = payload.get("case")
    output_payload = payload.get("output")
    config = payload.get("config") or {}
    data_db_path = payload.get("data_db_path")
    meta_db_path = payload.get("meta_db_path") or DEFAULT_META_DB
    metric_set_id = payload.get("metric_set_id")

    if not run_id:
        raise HTTPException(status_code=400, detail="run_id is required")
    if not case_payload or not output_payload:
        raise HTTPException(status_code=400, detail="case and output are required")
    if not data_db_path:
        raise HTTPException(status_code=400, detail="data_db_path is required")

    try:
        raw_metrics, metric_set, aggregated_metrics = _evaluate_report_with_metric_set(
            case_payload,
            output_payload,
            config,
            data_db_path,
            metric_set_id=metric_set_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    run_config = {**config}
    if metric_set_id:
        run_config["metric_set_id"] = metric_set_id
    save_case_result(
        meta_db_path,
        run_id,
        case_payload.get("case_id", "case-unknown"),
        {
            "raw_metrics": raw_metrics,
            "aggregated_metrics": aggregated_metrics,
        },
        {
            "output": output_payload,
            "metric_set": _report_metric_set_summary(metric_set),
        },
    )
    case_results = [_normalize_report_case_result(item) for item in list_report_case_results(meta_db_path, run_id)]
    run_summary = summarize_report_run(metric_set, case_results, run_config)
    save_run(meta_db_path, run_id, run_config, run_summary)

    response = {
        "run_id": run_id,
        "run_summary": run_summary,
    }
    if metric_set:
        response.update(
            {
                "raw_metrics": raw_metrics,
                "applied_metric_set": _report_metric_set_summary(metric_set),
                "aggregated_metrics": aggregated_metrics,
            }
        )
    else:
        response["metrics"] = raw_metrics
    return response
