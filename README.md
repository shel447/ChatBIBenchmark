# ChatBI Benchmark (Report Evaluation MVP)

This repository contains a minimal implementation of the report-evaluation logic (structure + executable assertions) with a SQLite-backed metadata store and a clean UI mock.

## Setup

Install dependencies:

```
pip install -r requirements.txt
```

## Backend

- Core evaluator: `backend/core/evaluator.py`
- Query adapter: `backend/adapters/sqlite_adapter.py`
- Metadata store: `backend/storage/sqlite_store.py`
- Case set Excel import/export: `backend/adapters/excel_case_set_adapter.py`

Start the API:

```
python -m uvicorn backend.app:app --reload
```

Evaluate a case (example payload):

```
POST /api/report/evaluate
{
  "case": { ... },
  "output": { ... },
  "data_db_path": "C:/path/to/your/data.db",
  "config": {"n_turns": 5}
}
```

## Frontend

Visit `http://127.0.0.1:8005/frontend/` after starting the backend. The frontend is static and does not require a build step.

## Tests

Run tests with the project virtual environment:

```
.venv\Scripts\python.exe -m unittest tests/test_frontend_routes.py -v
.venv\Scripts\python.exe -m unittest tests/test_case_sets_api.py -v
.venv\Scripts\python.exe -m unittest tests/test_runs_api.py -v
```
