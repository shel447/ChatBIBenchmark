import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from ..domain.schedule import ScheduleJob
from ..ports.schedule_repository import ScheduleRepository
from ..ports.task_repository import TaskRepository
from .task_usecases import execute_task
from backend.storage.case_set_repository import SqliteCaseSetRepository
from backend.storage.run_repository import SqliteRunRepository, SqliteScheduleRepository, SqliteTaskRepository


DEFAULT_TIMEZONE = "Asia/Shanghai"
SHANGHAI_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
VALID_SCHEDULE_TYPES = {"one_time", "daily"}
VALID_SCHEDULE_STATUSES = {"enabled", "paused", "completed"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _resolve_timezone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        if timezone_name == DEFAULT_TIMEZONE:
            return SHANGHAI_TZ
        raise


def _parse_run_at(run_at: str, timezone_name: str) -> datetime:
    value = datetime.fromisoformat(run_at)
    if value.tzinfo is None:
        value = value.replace(tzinfo=_resolve_timezone(timezone_name))
    return value.astimezone(timezone.utc)


def _compute_next_daily_trigger(daily_time: str, timezone_name: str, now: Optional[datetime] = None) -> datetime:
    now_utc = now or _utc_now()
    local_now = now_utc.astimezone(_resolve_timezone(timezone_name))
    hour, minute = [int(part) for part in daily_time.split(":", 1)]
    candidate = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= local_now:
        candidate = candidate + timedelta(days=1)
    return candidate.astimezone(timezone.utc)


def _next_trigger_for_schedule(schedule_type: str, timezone_name: str, run_at: Optional[str], daily_time: Optional[str], now: Optional[datetime] = None) -> Optional[str]:
    if schedule_type == "one_time":
        if not run_at:
            raise ValueError("run_at is required")
        return _to_utc_iso(_parse_run_at(run_at, timezone_name))
    if schedule_type == "daily":
        if not daily_time:
            raise ValueError("daily_time is required")
        return _to_utc_iso(_compute_next_daily_trigger(daily_time, timezone_name, now))
    raise ValueError("invalid schedule_type")


def create_schedule(
    schedule_repo: ScheduleRepository,
    task_repo: TaskRepository,
    name: str,
    task_id: str,
    schedule_type: str,
    run_at: Optional[str],
    daily_time: Optional[str],
    schedule_status: str,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> ScheduleJob:
    if schedule_type not in VALID_SCHEDULE_TYPES:
        raise ValueError("invalid schedule_type")
    if schedule_status not in VALID_SCHEDULE_STATUSES:
        raise ValueError("invalid schedule_status")
    task = task_repo.get(task_id)
    if not task:
        raise LookupError("task not found")
    if task.launch_mode != "deferred":
        raise ValueError("schedule can only bind deferred tasks")
    if schedule_repo.get_active_for_task(task_id):
        raise ValueError("task already has an active schedule")

    now = _utc_now()
    schedule = ScheduleJob(
        schedule_id=str(uuid.uuid4()),
        name=name,
        task_id=task_id,
        schedule_type=schedule_type,
        run_at=run_at,
        daily_time=daily_time,
        timezone=timezone_name,
        schedule_status=schedule_status,
        last_triggered_at=None,
        next_triggered_at=None if schedule_status != "enabled" else _next_trigger_for_schedule(schedule_type, timezone_name, run_at, daily_time, now),
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )
    schedule_repo.create(schedule)
    if task.task_status == "pending" and schedule.schedule_status == "enabled":
        task.task_status = "scheduled"
        task.updated_at = now.isoformat()
        task_repo.update(task)
    return schedule


def list_schedules(schedule_repo: ScheduleRepository, limit: int = 100) -> List[ScheduleJob]:
    return schedule_repo.list(limit)


def get_schedule(schedule_repo: ScheduleRepository, schedule_id: str) -> Optional[ScheduleJob]:
    return schedule_repo.get(schedule_id)


def update_schedule(
    schedule_repo: ScheduleRepository,
    task_repo: TaskRepository,
    schedule_id: str,
    schedule_status: Optional[str] = None,
    run_at: Optional[str] = None,
    daily_time: Optional[str] = None,
) -> ScheduleJob:
    schedule = schedule_repo.get(schedule_id)
    if not schedule:
        raise LookupError("schedule not found")
    if schedule_status:
        if schedule_status not in VALID_SCHEDULE_STATUSES:
            raise ValueError("invalid schedule_status")
        schedule.schedule_status = schedule_status
    if run_at is not None:
        schedule.run_at = run_at
    if daily_time is not None:
        schedule.daily_time = daily_time
    now = _utc_now()
    if schedule.schedule_status == "enabled":
        schedule.next_triggered_at = _next_trigger_for_schedule(
            schedule.schedule_type,
            schedule.timezone,
            schedule.run_at,
            schedule.daily_time,
            now,
        )
    elif schedule.schedule_status == "completed":
        schedule.next_triggered_at = None
    schedule.updated_at = now.isoformat()
    schedule_repo.update(schedule)

    task = task_repo.get(schedule.task_id)
    if task and task.launch_mode == "deferred":
        task.task_status = "scheduled" if schedule.schedule_status == "enabled" else "pending"
        task.updated_at = now.isoformat()
        task_repo.update(task)
    return schedule


def delete_schedule(schedule_repo: ScheduleRepository, task_repo: TaskRepository, schedule_id: str) -> None:
    schedule = schedule_repo.get(schedule_id)
    if not schedule:
        return
    task = task_repo.get(schedule.task_id)
    if task and task.launch_mode == "deferred":
        task.task_status = "pending"
        task.updated_at = _utc_now().isoformat()
        task_repo.update(task)
    schedule_repo.delete(schedule_id)


def process_due_schedules(db_path: str, case_set_db_path: Optional[str] = None, now: Optional[datetime] = None) -> int:
    now_dt = now.astimezone(timezone.utc) if now else _utc_now()
    schedule_repo = SqliteScheduleRepository(db_path)
    task_repo = SqliteTaskRepository(db_path)
    run_repo = SqliteRunRepository(db_path)
    case_set_repo = SqliteCaseSetRepository(case_set_db_path) if case_set_db_path else None
    due_items = schedule_repo.list_due(now_dt.isoformat())
    processed = 0

    for schedule in due_items:
        task = task_repo.get(schedule.task_id)
        if not task:
            continue
        task, run = execute_task(task_repo, run_repo, task.task_id, trigger_source="schedule")
        if case_set_repo:
            materialize_execution_results(run_repo, task_repo, case_set_repo, run.run_id)
        processed += 1
        schedule.last_triggered_at = now_dt.isoformat()
        if schedule.schedule_type == "one_time":
            schedule.schedule_status = "completed"
            schedule.next_triggered_at = None
        else:
            next_local = _compute_next_daily_trigger(schedule.daily_time or "00:00", schedule.timezone, now_dt + timedelta(seconds=1))
            schedule.next_triggered_at = _to_utc_iso(next_local)
        schedule.updated_at = now_dt.isoformat()
        schedule_repo.update(schedule)

    return processed
