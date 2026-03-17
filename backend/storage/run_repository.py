import sqlite3
from typing import List, Optional

from backend.core.domain.run import Run


SCHEMA = """
create table if not exists eval_run (
  run_id text primary key,
  name text not null,
  case_set_id text not null,
  environment_id text not null,
  metric_set_id text not null,
  repeat_count integer not null,
  total_cases integer not null,
  executed_cases integer not null,
  accuracy real not null,
  status text not null,
  started_at text not null,
  ended_at text
);
"""


def init_run_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


class SqliteRunRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, run: Run) -> Run:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "insert into eval_run(run_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, started_at, ended_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.run_id,
                    run.name,
                    run.case_set_id,
                    run.environment_id,
                    run.metric_set_id,
                    run.repeat_count,
                    run.total_cases,
                    run.executed_cases,
                    run.accuracy,
                    run.status,
                    run.started_at,
                    run.ended_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return run

    def list(self, limit: int = 50) -> List[Run]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, started_at, ended_at "
                "from eval_run order by started_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [
            Run(
                run_id=row[0],
                name=row[1],
                case_set_id=row[2],
                environment_id=row[3],
                metric_set_id=row[4],
                repeat_count=row[5],
                total_cases=row[6],
                executed_cases=row[7],
                accuracy=row[8],
                status=row[9],
                started_at=row[10],
                ended_at=row[11],
            )
            for row in rows
        ]

    def get(self, run_id: str) -> Optional[Run]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, started_at, ended_at "
                "from eval_run where run_id = ?",
                (run_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        if not row:
            return None
        return Run(
            run_id=row[0],
            name=row[1],
            case_set_id=row[2],
            environment_id=row[3],
            metric_set_id=row[4],
            repeat_count=row[5],
            total_cases=row[6],
            executed_cases=row[7],
            accuracy=row[8],
            status=row[9],
            started_at=row[10],
            ended_at=row[11],
        )
