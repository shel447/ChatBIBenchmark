from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence


SUPPORTED_REPORT_DIMENSIONS: Dict[str, Dict[str, object]] = {
    "template_top1_accuracy": {
        "source": "template.top1",
        "formula": "raw.template.top1",
        "required_any_case_fields": (("template_name", "expected_template_id"),),
    },
    "param_slot_f1": {
        "source": "params.f1",
        "formula": "raw.params.f1",
        "required_case_fields": ("param_ground_truth",),
    },
    "task_success_rate": {
        "source": "completion.completed + delivery.report_generated",
        "formula": "1.0 if raw.completion.completed and raw.delivery.report_generated else 0.0",
        "required_case_fields": (),
    },
    "turn_efficiency": {
        "source": "completion.turns_used",
        "formula": "0.0 if task_success_rate == 0 else (n_turns - turns_used + 1) / n_turns",
        "required_case_fields": (),
    },
    "outline_structure_f1": {
        "source": "outline.f1",
        "formula": "raw.outline.f1",
        "required_case_fields": ("outline_ground_truth",),
    },
    "factual_precision": {
        "source": "content.pass_rate",
        "formula": "raw.content.pass_rate",
        "required_case_fields": ("content_assertions",),
    },
}

ACTIVE_SCENARIO_TYPE = "报告多轮交互"


def supported_report_dimension_keys() -> List[str]:
    return list(SUPPORTED_REPORT_DIMENSIONS.keys())


def is_report_metric_set_supported(dimensions: Sequence[Dict[str, object]]) -> bool:
    if not dimensions:
        return False
    dimension_keys = [str(item.get("key") or "") for item in dimensions]
    return all(key in SUPPORTED_REPORT_DIMENSIONS for key in dimension_keys)


def validate_report_dimension_keys(dimensions: Sequence[Dict[str, object]]) -> None:
    unsupported = [
        str(item.get("key") or "")
        for item in dimensions
        if str(item.get("key") or "") not in SUPPORTED_REPORT_DIMENSIONS
    ]
    if unsupported:
        joined = ", ".join(unsupported)
        raise ValueError(f"unsupported report metric dimensions: {joined}")


def execution_status_for_metric_set(metric_set) -> Dict[str, object]:
    supported = []
    unsupported = []
    for dimension in metric_set.dimensions:
        key = str(dimension.get("key") or "")
        if key in SUPPORTED_REPORT_DIMENSIONS and metric_set.scenario_type == ACTIVE_SCENARIO_TYPE:
            supported.append(key)
        else:
            unsupported.append(key)
    status = "active" if metric_set.scenario_type == ACTIVE_SCENARIO_TYPE and not unsupported else "planned"
    return {
        "status": status,
        "supported_dimension_keys": supported,
        "unsupported_dimension_keys": unsupported,
    }


def execution_mapping_for_metric_set(metric_set) -> List[Dict[str, object]]:
    mappings = []
    for dimension in metric_set.dimensions:
        key = str(dimension.get("key") or "")
        spec = SUPPORTED_REPORT_DIMENSIONS.get(key)
        mappings.append(
            {
                "key": key,
                "name": dimension.get("name"),
                "source": spec["source"] if spec else "未接入执行",
                "formula": spec["formula"] if spec else "仅配置，未接入执行",
                "hard_gate": bool(dimension.get("hard_gate")),
                "target": dimension.get("target"),
                "supported": bool(spec) and metric_set.scenario_type == ACTIVE_SCENARIO_TYPE,
            }
        )
    return mappings


def validate_report_case_requirements(metric_set, case_payload: Dict[str, object]) -> None:
    missing_fields = set()
    for dimension in metric_set.dimensions:
        spec = SUPPORTED_REPORT_DIMENSIONS.get(str(dimension.get("key") or ""))
        if not spec:
            continue
        for field_group in spec.get("required_case_fields", ()):
            if field_group == "content_assertions":
                assertions = case_payload.get("content_assertions") or []
                if not assertions:
                    missing_fields.add("content_assertions")
                continue
            if not case_payload.get(field_group):
                missing_fields.add(field_group)
        for any_field_group in spec.get("required_any_case_fields", ()):
            if not any(case_payload.get(field_name) for field_name in any_field_group):
                missing_fields.add("/".join(any_field_group))
    if missing_fields:
        ordered = ", ".join(sorted(missing_fields))
        raise ValueError(f"missing required report ground truth: {ordered}")


def resolve_report_dimension_value(key: str, raw_metrics: Dict[str, object], config: Optional[Dict[str, object]] = None) -> float:
    config = config or {}
    n_turns = int(config.get("n_turns", 5) or 5)
    if n_turns <= 0:
        n_turns = 5

    template = raw_metrics.get("template") or {}
    params = raw_metrics.get("params") or {}
    completion = raw_metrics.get("completion") or {}
    outline = raw_metrics.get("outline") or {}
    content = raw_metrics.get("content") or {}
    delivery = raw_metrics.get("delivery") or {}

    if key == "template_top1_accuracy":
        return float(template.get("top1", 0.0) or 0.0)
    if key == "param_slot_f1":
        return float(params.get("f1", 0.0) or 0.0)
    if key == "task_success_rate":
        completed = bool(completion.get("completed"))
        report_generated = bool(delivery.get("report_generated"))
        return 1.0 if completed and report_generated else 0.0
    if key == "turn_efficiency":
        task_success_rate = resolve_report_dimension_value("task_success_rate", raw_metrics, config)
        if task_success_rate <= 0:
            return 0.0
        turns_used = int(completion.get("turns_used", n_turns) or n_turns)
        return max(0.0, min(1.0, float(n_turns - turns_used + 1) / float(n_turns)))
    if key == "outline_structure_f1":
        return float(outline.get("f1", 0.0) or 0.0)
    if key == "factual_precision":
        return float(content.get("pass_rate", 0.0) or 0.0)
    raise ValueError(f"unsupported report metric dimension: {key}")


def aggregate_report_metric_set(metric_set, raw_metrics: Dict[str, object], config: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    config = config or {}
    total_weight = sum(float(dimension.get("weight", 0.0) or 0.0) for dimension in metric_set.dimensions)
    if total_weight <= 0:
        raise ValueError("dimensions weight sum must be positive")

    dimension_results = []
    hard_gate_passed = True
    weighted_sum = 0.0

    for dimension in metric_set.dimensions:
        key = str(dimension.get("key") or "")
        raw_value = resolve_report_dimension_value(key, raw_metrics, config)
        weight = float(dimension.get("weight", 0.0) or 0.0)
        target = float(dimension.get("target", 0.0) or 0.0)
        hard_gate = bool(dimension.get("hard_gate"))
        target_passed = raw_value >= target
        score_contribution = (raw_value * weight) / total_weight if total_weight else 0.0
        if hard_gate and not target_passed:
            hard_gate_passed = False
        weighted_sum += raw_value * weight
        dimension_results.append(
            {
                "key": key,
                "name": dimension.get("name"),
                "raw_value": raw_value,
                "target": target,
                "weight": weight,
                "hard_gate": hard_gate,
                "target_passed": target_passed,
                "score_contribution": score_contribution,
            }
        )

    overall_score = weighted_sum / total_weight
    threshold_passed = overall_score >= float(metric_set.pass_threshold)
    return {
        "scenario_type": metric_set.scenario_type,
        "score_formula": metric_set.score_formula,
        "pass_threshold": float(metric_set.pass_threshold),
        "overall_score": overall_score,
        "hard_gate_passed": hard_gate_passed,
        "threshold_passed": threshold_passed,
        "passed": hard_gate_passed and threshold_passed,
        "dimensions": dimension_results,
    }


def summarize_raw_metrics(raw_metrics_list: Iterable[Dict[str, object]]) -> Dict[str, object]:
    items = list(raw_metrics_list)
    if not items:
        return {}

    count = len(items)

    def average(path: Sequence[str]) -> float:
        total = 0.0
        for item in items:
            value = item
            for part in path:
                value = (value or {}).get(part) if isinstance(value, dict) else None
            total += float(value or 0.0)
        return total / count

    return {
        "template": {
            "top1": average(("template", "top1")),
            "topk": average(("template", "topk")),
        },
        "params": {
            "precision": average(("params", "precision")),
            "recall": average(("params", "recall")),
            "f1": average(("params", "f1")),
        },
        "completion": {
            "completed_rate": average(("completion", "completed")),
            "avg_turns_used": average(("completion", "turns_used")),
        },
        "outline": {
            "precision": average(("outline", "precision")),
            "recall": average(("outline", "recall")),
            "f1": average(("outline", "f1")),
        },
        "content": {
            "pass_rate": average(("content", "pass_rate")),
            "fail_rate": average(("content", "fail_rate")),
            "missing_rate": average(("content", "missing_rate")),
            "error_rate": average(("content", "error_rate")),
        },
        "delivery": {
            "report_generated_rate": average(("delivery", "report_generated")),
        },
        "overall_score": average(("overall_score",)),
    }


def summarize_report_run(metric_set, case_results: Sequence[Dict[str, object]], config: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    config = config or {}
    raw_metrics_list = [item.get("raw_metrics") or {} for item in case_results]
    raw_summary = summarize_raw_metrics(raw_metrics_list)
    aggregated_summary = None
    if metric_set and raw_summary:
        synthetic_raw_metrics = {
            "template": raw_summary.get("template", {}),
            "params": raw_summary.get("params", {}),
            "completion": {
                "completed": (raw_summary.get("completion", {}).get("completed_rate", 0.0) or 0.0) >= 0.999,
                "turns_used": raw_summary.get("completion", {}).get("avg_turns_used", 0.0) or 0.0,
            },
            "outline": raw_summary.get("outline", {}),
            "content": raw_summary.get("content", {}),
            "delivery": {
                "report_generated": (raw_summary.get("delivery", {}).get("report_generated_rate", 0.0) or 0.0) >= 0.999,
            },
            "overall_score": raw_summary.get("overall_score", 0.0),
        }

        average_by_key: Dict[str, float] = {}
        for dimension in metric_set.dimensions:
            key = str(dimension.get("key") or "")
            total = 0.0
            for case_result in case_results:
                aggregated_metrics = case_result.get("aggregated_metrics") or {}
                dimension_map = {
                    str(item.get("key") or ""): float(item.get("raw_value", 0.0) or 0.0)
                    for item in aggregated_metrics.get("dimensions", [])
                }
                total += dimension_map.get(key, resolve_report_dimension_value(key, case_result.get("raw_metrics") or {}, config))
            average_by_key[key] = total / len(case_results)

        dimension_results = []
        total_weight = sum(float(item.get("weight", 0.0) or 0.0) for item in metric_set.dimensions)
        weighted_sum = 0.0
        hard_gate_passed = True
        for dimension in metric_set.dimensions:
            key = str(dimension.get("key") or "")
            raw_value = average_by_key[key]
            weight = float(dimension.get("weight", 0.0) or 0.0)
            target = float(dimension.get("target", 0.0) or 0.0)
            hard_gate = bool(dimension.get("hard_gate"))
            target_passed = raw_value >= target
            if hard_gate and not target_passed:
                hard_gate_passed = False
            weighted_sum += raw_value * weight
            dimension_results.append(
                {
                    "key": key,
                    "name": dimension.get("name"),
                    "raw_value": raw_value,
                    "target": target,
                    "weight": weight,
                    "hard_gate": hard_gate,
                    "target_passed": target_passed,
                    "score_contribution": (raw_value * weight) / total_weight if total_weight else 0.0,
                }
            )
        overall_score = weighted_sum / total_weight if total_weight else 0.0
        threshold_passed = overall_score >= float(metric_set.pass_threshold)
        aggregated_summary = {
            "scenario_type": metric_set.scenario_type,
            "score_formula": metric_set.score_formula,
            "pass_threshold": float(metric_set.pass_threshold),
            "overall_score": overall_score,
            "hard_gate_passed": hard_gate_passed,
            "threshold_passed": threshold_passed,
            "passed": hard_gate_passed and threshold_passed,
            "dimensions": dimension_results,
        }
    return {
        "raw_summary": raw_summary,
        "aggregated_summary": aggregated_summary,
        "case_count": len(case_results),
    }
