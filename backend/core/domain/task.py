from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    task_id: str
    name: str
    case_set_id: str
    environment_id: str
    metric_set_id: str
    repeat_count: int
    launch_mode: str
    task_status: str
    created_at: str
    updated_at: str
    latest_execution_id: Optional[str]
