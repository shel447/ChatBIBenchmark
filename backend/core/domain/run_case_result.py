from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RunCaseResult:
    run_id: str
    task_id: Optional[str]
    case_set_id: str
    case_id: str
    case_title: str
    case_type: str
    accuracy: float
    status: str
    issue_tags: List[str]
    detail_metrics: dict
    summary: str
    created_at: str
    updated_at: str
