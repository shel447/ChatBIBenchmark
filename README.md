# ChatBI Benchmark (Report Evaluation MVP)

This repository contains a minimal implementation of the report-evaluation logic (structure + executable assertions) with a SQLite-backed metadata store and a clean UI mock.

## Backend

- Core evaluator: `backend/core/evaluator.py`
- Query adapter: `backend/adapters/sqlite_adapter.py`
- Metadata store: `backend/storage/sqlite_store.py`

Start the API (requires FastAPI installed):

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

Open `frontend/index.html` in a browser. It is a clean static UI mock (no build step).

## Tests

Run evaluator tests using the local Python path:

```
C:\Users\Administrator\AppData\Roaming\uv\python\cpython-3.14.3-windows-x86_64-none\python.exe -m unittest tests/test_report_evaluator.py -v
```
