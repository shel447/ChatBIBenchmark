import json
import sqlite3
from datetime import datetime, timezone


SCHEMA = """
create table if not exists report_run (
  run_id text primary key,
  created_at text not null,
  config_json text,
  metrics_json text
);

create table if not exists report_case_result (
  run_id text not null,
  case_id text not null,
  metrics_json text,
  details_json text,
  primary key (run_id, case_id)
);
"""


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def save_run(db_path, run_id, config, metrics):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "insert or replace into report_run(run_id, created_at, config_json, metrics_json) values (?, ?, ?, ?)",
            (
                run_id,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(config or {}),
                json.dumps(metrics or {}),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def save_case_result(db_path, run_id, case_id, metrics, details):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "insert or replace into report_case_result(run_id, case_id, metrics_json, details_json) values (?, ?, ?, ?)",
            (
                run_id,
                case_id,
                json.dumps(metrics or {}),
                json.dumps(details or {}),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_run(db_path, run_id):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "select run_id, created_at, config_json, metrics_json from report_run where run_id = ?",
            (run_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "run_id": row[0],
            "created_at": row[1],
            "config": json.loads(row[2] or "{}"),
            "metrics": json.loads(row[3] or "{}"),
        }
    finally:
        conn.close()


def list_runs(db_path, limit=50):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "select run_id, created_at, config_json, metrics_json from report_run order by created_at desc limit ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            {
                "run_id": row[0],
                "created_at": row[1],
                "config": json.loads(row[2] or "{}"),
                "metrics": json.loads(row[3] or "{}"),
            }
            for row in rows
        ]
    finally:
        conn.close()
