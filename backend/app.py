import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .core.evaluator import evaluate_report_case
from .adapters.sqlite_adapter import SQLiteAdapter
from .storage.sqlite_store import init_db, save_run, save_case_result

APP_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "frontend"))
DATA_DIR = os.path.join(APP_DIR, "data")
DEFAULT_META_DB = os.path.join(APP_DIR, "report_eval.db")

app = FastAPI(title="ChatBI Report Eval")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.on_event("startup")
async def _startup():
    init_db(DEFAULT_META_DB)


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
