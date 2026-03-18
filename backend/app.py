import json
import os

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from .core.evaluator import evaluate_report_case
from .core.usecases.case_set_usecases import export_case_set, get_case_set_detail, import_case_set, list_case_sets
from .core.usecases.run_usecases import create_run, get_run, list_runs
from .adapters.sqlite_adapter import SQLiteAdapter
from .storage.case_set_repository import SqliteCaseSetRepository, init_case_set_db
from .storage.sqlite_store import init_db, save_run, save_case_result
from .storage.run_repository import SqliteRunRepository, init_run_db

APP_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "frontend"))
DATA_DIR = os.path.join(APP_DIR, "data")
DEFAULT_META_DB = os.path.join(APP_DIR, "report_eval.db")
DEFAULT_RUN_DB = os.path.join(APP_DIR, "runs.db")
DEFAULT_CASE_SET_DB = os.path.join(APP_DIR, "case_sets.db")

app = FastAPI(title="ChatBI Report Eval")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.on_event("startup")
async def _startup():
    init_db(DEFAULT_META_DB)
    init_run_db(DEFAULT_RUN_DB)
    init_case_set_db(DEFAULT_CASE_SET_DB)


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


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


@app.post("/api/runs")
async def create_run_api(request: Request):
    payload = await request.json()
    required_fields = (
        "name",
        "case_set_id",
        "environment_id",
        "metric_set_id",
        "repeat_count",
    )
    for field in required_fields:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    run = create_run(
        repo,
        payload["name"],
        payload["case_set_id"],
        payload["environment_id"],
        payload["metric_set_id"],
        payload["repeat_count"],
    )
    return {"run": run.__dict__}


@app.get("/api/runs")
async def list_runs_api():
    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    runs = [run.__dict__ for run in list_runs(repo)]
    return {"runs": runs}


@app.get("/api/runs/{run_id}")
async def get_run_api(run_id: str):
    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    run = get_run(repo, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run": run.__dict__}


@app.post("/api/report/evaluate")
async def evaluate_case(request: Request):
    payload = await request.json()
    case_payload = payload.get("case")
    output_payload = payload.get("output")
    config = payload.get("config") or {}
    data_db_path = payload.get("data_db_path")

    if not case_payload or not output_payload:
        raise HTTPException(status_code=400, detail="case and output are required")
    if not data_db_path:
        raise HTTPException(status_code=400, detail="data_db_path is required")

    adapter = SQLiteAdapter(data_db_path)
    metrics = evaluate_report_case(case_payload, output_payload, adapter, config)
    return {"metrics": metrics}


@app.post("/api/report/runs")
async def evaluate_and_store_run(request: Request):
    payload = await request.json()
    run_id = payload.get("run_id")
    case_payload = payload.get("case")
    output_payload = payload.get("output")
    config = payload.get("config") or {}
    data_db_path = payload.get("data_db_path")
    meta_db_path = payload.get("meta_db_path") or DEFAULT_META_DB

    if not run_id:
        raise HTTPException(status_code=400, detail="run_id is required")
    if not case_payload or not output_payload:
        raise HTTPException(status_code=400, detail="case and output are required")
    if not data_db_path:
        raise HTTPException(status_code=400, detail="data_db_path is required")

    adapter = SQLiteAdapter(data_db_path)
    metrics = evaluate_report_case(case_payload, output_payload, adapter, config)

    save_run(meta_db_path, run_id, config, {"overall_score": metrics["overall_score"]})
    save_case_result(
        meta_db_path,
        run_id,
        case_payload.get("case_id", "case-unknown"),
        metrics,
        {"output": output_payload},
    )

    return {"run_id": run_id, "metrics": metrics}
