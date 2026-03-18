from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class MetricSet:
    metric_set_id: str
    name: str
    scenario_type: str
    description: str
    score_formula: str
    pass_threshold: float
    dimensions: List[Dict[str, Any]]
    benchmark_refs: List[Dict[str, Any]]
    created_at: str
    updated_at: str
