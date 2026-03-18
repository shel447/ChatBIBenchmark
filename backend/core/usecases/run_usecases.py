from typing import List, Optional

from ..domain.run import Run
from ..ports.run_repository import RunRepository


def list_runs(repo: RunRepository, limit: int = 50) -> List[Run]:
    return repo.list(limit)


def get_run(repo: RunRepository, run_id: str) -> Optional[Run]:
    return repo.get(run_id)
