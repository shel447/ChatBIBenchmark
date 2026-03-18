import sqlite3
from typing import List, Optional

from backend.core.domain.run import Run
from backend.core.domain.schedule import ScheduleJob
from backend.core.domain.task import Task


SCHEMA = """
create table if not exists eval_task (
  task_id text primary key,
  name text not null,
  case_set_id text not null,
  environment_id text not null,
  metric_set_id text not null,
  repeat_count integer not null,
  launch_mode text not null,
  task_status text not null,
  created_at text not null,
  updated_at text not null,
  latest_execution_id text
);

create table if not exists eval_run (
  run_id text primary key,
  task_id text,
  name text not null,
  case_set_id text not null,
  environment_id text not null,
  metric_set_id text not null,
  repeat_count integer not null,
  total_cases integer not null,
  executed_cases integer not null,
  accuracy real not null,
  status text not null default 'running',
  trigger_source text not null,
  execution_status text not null,
  started_at text not null,
  ended_at text
);

create table if not exists schedule_job (
  schedule_id text primary key,
  name text not null,
  task_id text not null,
  schedule_type text not null,
  run_at text,
  daily_time text,
  timezone text not null,
  schedule_status text not null,
  last_triggered_at text,
  next_triggered_at text,
  created_at text not null,
  updated_at text not null
);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    cur = conn.execute(f"pragma table_info({table_name})")
    columns = {row[1] for row in cur.fetchall()}
    if column_name not in columns:
        conn.execute(f"alter table {table_name} add column {column_name} {definition}")


def init_run_db(db_path: str) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA)
        _ensure_column(conn, "eval_run", "status", "text not null default 'running'")
        _ensure_column(conn, "eval_run", "task_id", "text")
        _ensure_column(conn, "eval_run", "trigger_source", "text not null default 'legacy'")
        _ensure_column(conn, "eval_run", "execution_status", "text not null default 'running'")
        conn.commit()
    finally:
        conn.close()


def _task_from_row(row) -> Task:
    return Task(
        task_id=row[0],
        name=row[1],
        case_set_id=row[2],
        environment_id=row[3],
        metric_set_id=row[4],
        repeat_count=row[5],
        launch_mode=row[6],
        task_status=row[7],
        created_at=row[8],
        updated_at=row[9],
        latest_execution_id=row[10],
    )


def _run_from_row(row) -> Run:
    return Run(
        run_id=row[0],
        task_id=row[1],
        name=row[2],
        case_set_id=row[3],
        environment_id=row[4],
        metric_set_id=row[5],
        repeat_count=row[6],
        total_cases=row[7],
        executed_cases=row[8],
        accuracy=row[9],
        trigger_source=row[10],
        execution_status=row[11],
        started_at=row[12],
        ended_at=row[13],
    )


def _schedule_from_row(row) -> ScheduleJob:
    return ScheduleJob(
        schedule_id=row[0],
        name=row[1],
        task_id=row[2],
        schedule_type=row[3],
        run_at=row[4],
        daily_time=row[5],
        timezone=row[6],
        schedule_status=row[7],
        last_triggered_at=row[8],
        next_triggered_at=row[9],
        created_at=row[10],
        updated_at=row[11],
    )


class SqliteTaskRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, task: Task) -> Task:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "insert into eval_task(task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, launch_mode, task_status, created_at, updated_at, latest_execution_id) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task.task_id,
                    task.name,
                    task.case_set_id,
                    task.environment_id,
                    task.metric_set_id,
                    task.repeat_count,
                    task.launch_mode,
                    task.task_status,
                    task.created_at,
                    task.updated_at,
                    task.latest_execution_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return task

    def update(self, task: Task) -> Task:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "update eval_task set name = ?, case_set_id = ?, environment_id = ?, metric_set_id = ?, repeat_count = ?, launch_mode = ?, task_status = ?, created_at = ?, updated_at = ?, latest_execution_id = ? where task_id = ?",
                (
                    task.name,
                    task.case_set_id,
                    task.environment_id,
                    task.metric_set_id,
                    task.repeat_count,
                    task.launch_mode,
                    task.task_status,
                    task.created_at,
                    task.updated_at,
                    task.latest_execution_id,
                    task.task_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return task

    def list(self, limit: int = 50) -> List[Task]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, launch_mode, task_status, created_at, updated_at, latest_execution_id "
                "from eval_task order by updated_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_task_from_row(row) for row in rows]

    def get(self, task_id: str) -> Optional[Task]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, launch_mode, task_status, created_at, updated_at, latest_execution_id "
                "from eval_task where task_id = ?",
                (task_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _task_from_row(row) if row else None


class SqliteRunRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, run: Run) -> Run:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "insert into eval_run(run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, trigger_source, execution_status, started_at, ended_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.run_id,
                    run.task_id,
                    run.name,
                    run.case_set_id,
                    run.environment_id,
                    run.metric_set_id,
                    run.repeat_count,
                    run.total_cases,
                    run.executed_cases,
                    run.accuracy,
                    run.execution_status,
                    run.trigger_source,
                    run.execution_status,
                    run.started_at,
                    run.ended_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return run

    def list(self, limit: int = 50) -> List[Run]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, trigger_source, execution_status, started_at, ended_at "
                "from eval_run order by started_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_run_from_row(row) for row in rows]

    def list_by_task(self, task_id: str, limit: int = 50) -> List[Run]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, trigger_source, execution_status, started_at, ended_at "
                "from eval_run where task_id = ? order by started_at desc limit ?",
                (task_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_run_from_row(row) for row in rows]

    def get(self, run_id: str) -> Optional[Run]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, trigger_source, execution_status, started_at, ended_at "
                "from eval_run where run_id = ?",
                (run_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _run_from_row(row) if row else None


class SqliteScheduleRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, schedule: ScheduleJob) -> ScheduleJob:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "insert into schedule_job(schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    schedule.schedule_id,
                    schedule.name,
                    schedule.task_id,
                    schedule.schedule_type,
                    schedule.run_at,
                    schedule.daily_time,
                    schedule.timezone,
                    schedule.schedule_status,
                    schedule.last_triggered_at,
                    schedule.next_triggered_at,
                    schedule.created_at,
                    schedule.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return schedule

    def update(self, schedule: ScheduleJob) -> ScheduleJob:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "update schedule_job set name = ?, task_id = ?, schedule_type = ?, run_at = ?, daily_time = ?, timezone = ?, schedule_status = ?, last_triggered_at = ?, next_triggered_at = ?, created_at = ?, updated_at = ? where schedule_id = ?",
                (
                    schedule.name,
                    schedule.task_id,
                    schedule.schedule_type,
                    schedule.run_at,
                    schedule.daily_time,
                    schedule.timezone,
                    schedule.schedule_status,
                    schedule.last_triggered_at,
                    schedule.next_triggered_at,
                    schedule.created_at,
                    schedule.updated_at,
                    schedule.schedule_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return schedule

    def delete(self, schedule_id: str) -> None:
        conn = _connect(self.db_path)
        try:
            conn.execute("delete from schedule_job where schedule_id = ?", (schedule_id,))
            conn.commit()
        finally:
            conn.close()

    def list(self, limit: int = 100) -> List[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job order by created_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_schedule_from_row(row) for row in rows]

    def list_due(self, now_iso: str) -> List[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job where schedule_status = 'enabled' and next_triggered_at is not null and next_triggered_at <= ? order by next_triggered_at asc",
                (now_iso,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_schedule_from_row(row) for row in rows]

    def get(self, schedule_id: str) -> Optional[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job where schedule_id = ?",
                (schedule_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _schedule_from_row(row) if row else None

    def get_active_for_task(self, task_id: str) -> Optional[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job where task_id = ? and schedule_status = 'enabled' order by created_at desc limit 1",
                (task_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _schedule_from_row(row) if row else None
