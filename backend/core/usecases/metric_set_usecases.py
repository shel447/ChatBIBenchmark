import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..domain.metric_set import MetricSet
from ..ports.metric_set_repository import MetricSetRepository


VALID_SCENARIO_TYPES = {"通用", "NL2SQL", "NL2CHART", "报告多轮交互", "智能问数"}
VALID_SCORE_FORMULAS = {"weighted_sum", "weighted_sum_with_gates"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_dimension(dimension: Dict[str, object]) -> None:
    required_fields = ("key", "name", "measurement", "weight", "target", "hard_gate", "business_value")
    for field in required_fields:
        if field not in dimension:
            raise ValueError(f"dimension.{field} is required")


def _validate_metric_set_payload(
    scenario_type: str,
    score_formula: str,
    pass_threshold: float,
    dimensions: List[Dict[str, object]],
) -> None:
    if scenario_type not in VALID_SCENARIO_TYPES:
        raise ValueError("invalid scenario_type")
    if score_formula not in VALID_SCORE_FORMULAS:
        raise ValueError("invalid score_formula")
    if not 0 <= float(pass_threshold) <= 1:
        raise ValueError("pass_threshold must be between 0 and 1")
    if not dimensions:
        raise ValueError("dimensions is required")
    total_weight = 0.0
    for dimension in dimensions:
        _validate_dimension(dimension)
        total_weight += float(dimension["weight"])
    if total_weight <= 0:
        raise ValueError("dimensions weight sum must be positive")


def _metric_set_to_dict(metric_set: MetricSet) -> Dict[str, object]:
    return {
        "metric_set_id": metric_set.metric_set_id,
        "name": metric_set.name,
        "scenario_type": metric_set.scenario_type,
        "description": metric_set.description,
        "score_formula": metric_set.score_formula,
        "pass_threshold": metric_set.pass_threshold,
        "dimensions": metric_set.dimensions,
        "benchmark_refs": metric_set.benchmark_refs,
        "created_at": metric_set.created_at,
        "updated_at": metric_set.updated_at,
    }


def list_metric_sets(repo: MetricSetRepository) -> List[Dict[str, object]]:
    return [_metric_set_to_dict(metric_set) for metric_set in repo.list()]


def get_metric_set(repo: MetricSetRepository, metric_set_id: str) -> Optional[Dict[str, object]]:
    metric_set = repo.get(metric_set_id)
    return _metric_set_to_dict(metric_set) if metric_set else None


def create_metric_set(
    repo: MetricSetRepository,
    name: str,
    scenario_type: str,
    description: str,
    score_formula: str,
    pass_threshold: float,
    dimensions: List[Dict[str, object]],
    benchmark_refs: List[Dict[str, object]],
) -> Dict[str, object]:
    _validate_metric_set_payload(scenario_type, score_formula, pass_threshold, dimensions)
    now = _utc_now()
    metric_set = MetricSet(
        metric_set_id=f"metric-{uuid.uuid4().hex[:12]}",
        name=name,
        scenario_type=scenario_type,
        description=description,
        score_formula=score_formula,
        pass_threshold=float(pass_threshold),
        dimensions=dimensions,
        benchmark_refs=benchmark_refs,
        created_at=now,
        updated_at=now,
    )
    return _metric_set_to_dict(repo.create(metric_set))


def update_metric_set(
    repo: MetricSetRepository,
    metric_set_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    pass_threshold: Optional[float] = None,
    dimensions: Optional[List[Dict[str, object]]] = None,
) -> Dict[str, object]:
    metric_set = repo.get(metric_set_id)
    if not metric_set:
        raise LookupError("metric_set not found")
    if name is not None:
        metric_set.name = name
    if description is not None:
        metric_set.description = description
    if pass_threshold is not None:
        metric_set.pass_threshold = float(pass_threshold)
    if dimensions is not None:
        metric_set.dimensions = dimensions
    _validate_metric_set_payload(
        metric_set.scenario_type,
        metric_set.score_formula,
        metric_set.pass_threshold,
        metric_set.dimensions,
    )
    metric_set.updated_at = _utc_now()
    return _metric_set_to_dict(repo.update(metric_set))
