import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from ..domain.run import Run
from ..domain.task import Task
from ..ports.run_repository import RunRepository
from ..ports.task_repository import TaskRepository


VALID_LAUNCH_MODES = {"immediate", "deferred"}
VALID_TASK_STATUSES = {"pending", "scheduled", "running", "succeeded", "failed"}
VALID_TRIGGER_SOURCES = {"immediate_create", "manual", "schedule", "legacy"}
VALID_EXECUTION_STATUSES = {"running", "succeeded", "failed"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_execution(task: Task, trigger_source: str) -> Run:
    if trigger_source not in VALID_TRIGGER_SOURCES:
        raise ValueError("invalid trigger_source")
    return Run(
        run_id=str(uuid.uuid4()),
        task_id=task.task_id,
        name=task.name,
        case_set_id=task.case_set_id,
        environment_id=task.environment_id,
        metric_set_id=task.metric_set_id,
        repeat_count=task.repeat_count,
        total_cases=0,
        executed_cases=0,
        accuracy=0,
        trigger_source=trigger_source,
        execution_status="running",
        started_at=_utc_now(),
        ended_at=None,
    )


def create_task(
    task_repo: TaskRepository,
    run_repo: RunRepository,
    name: str,
    case_set_id: str,
    environment_id: str,
    metric_set_id: str,
    repeat_count: int,
    launch_mode: str,
) -> Tuple[Task, Optional[Run]]:
    if launch_mode not in VALID_LAUNCH_MODES:
        raise ValueError("invalid launch_mode")
    now = _utc_now()
    task = Task(
        task_id=str(uuid.uuid4()),
        name=name,
        case_set_id=case_set_id,
        environment_id=environment_id,
        metric_set_id=metric_set_id,
        repeat_count=repeat_count,
        launch_mode=launch_mode,
        task_status="pending" if launch_mode == "deferred" else "running",
        created_at=now,
        updated_at=now,
        latest_execution_id=None,
    )
    task_repo.create(task)
    if launch_mode == "deferred":
        return task, None

    run = _build_execution(task, "immediate_create")
    run_repo.create(run)
    task.latest_execution_id = run.run_id
    task.updated_at = _utc_now()
    task_repo.update(task)
    return task, run


def execute_task(task_repo: TaskRepository, run_repo: RunRepository, task_id: str, trigger_source: str = "manual") -> Tuple[Task, Run]:
    task = task_repo.get(task_id)
    if not task:
        raise LookupError("task not found")
    run = _build_execution(task, trigger_source)
    run_repo.create(run)
    task.latest_execution_id = run.run_id
    task.task_status = "running"
    task.updated_at = _utc_now()
    task_repo.update(task)
    return task, run


def list_tasks(task_repo: TaskRepository, limit: int = 50) -> List[Task]:
    return task_repo.list(limit)


def get_task(task_repo: TaskRepository, task_id: str) -> Optional[Task]:
    return task_repo.get(task_id)


def list_task_executions(run_repo: RunRepository, task_id: str, limit: int = 50) -> List[Run]:
    return run_repo.list_by_task(task_id, limit)
