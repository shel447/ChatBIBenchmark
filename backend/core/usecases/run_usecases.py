import uuid
from datetime import datetime, timezone
from typing import List, Optional

from ..domain.run import Run
from ..ports.run_repository import RunRepository


def create_run(
    repo: RunRepository,
    name: str,
    case_set_id: str,
    environment_id: str,
    metric_set_id: str,
    repeat_count: int,
) -> Run:
    run = Run(
        run_id=str(uuid.uuid4()),
        name=name,
        case_set_id=case_set_id,
        environment_id=environment_id,
        metric_set_id=metric_set_id,
        repeat_count=repeat_count,
        total_cases=0,
        executed_cases=0,
        accuracy=0,
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
        ended_at=None,
    )
    return repo.create(run)


def list_runs(repo: RunRepository, limit: int = 50) -> List[Run]:
    return repo.list(limit)


def get_run(repo: RunRepository, run_id: str) -> Optional[Run]:
    return repo.get(run_id)
