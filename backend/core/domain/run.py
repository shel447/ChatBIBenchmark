from dataclasses import dataclass
from typing import Optional


@dataclass
class Run:
    run_id: str
    name: str
    case_set_id: str
    environment_id: str
    metric_set_id: str
    repeat_count: int
    total_cases: int
    executed_cases: int
    accuracy: float
    status: str
    started_at: str
    ended_at: Optional[str]
