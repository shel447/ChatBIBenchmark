from .metrics import safe_div, f1
from .normalization import normalize_param_map, normalize_fact_value
from .outline import flatten_outline_paths

DEFAULT_TURNS = 5


def score_template(expected_template_id, predicted_template_id, predicted_ranked_ids=None, k=3):
    top1 = 1.0 if predicted_template_id == expected_template_id else 0.0
    ranked = predicted_ranked_ids or (
        [predicted_template_id] if predicted_template_id is not None else []
    )
    topk = 1.0 if expected_template_id in ranked[:k] else 0.0
    return {"top1": top1, "topk": topk}


def _values_match(expected, actual, tolerance=None):
    if expected is None and actual is None:
        return True
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        tol = tolerance if tolerance is not None else 0.0
        return abs(expected - actual) <= tol
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        return set(expected) == set(actual)
    return expected == actual


def score_params(ground_truth, filled_params):
    expected = normalize_param_map(ground_truth)
    actual = normalize_param_map(filled_params)

    expected_keys = set(expected.keys())
    actual_keys = set(actual.keys())

    correct = 0
    per_param = []
    for key in actual_keys:
        match = False
        if key in expected:
            match = _values_match(expected[key], actual[key])
        per_param.append({"param": key, "match": match})
        if match:
            correct += 1

    precision = safe_div(correct, len(actual_keys), zero_value=0.0)
    recall = safe_div(correct, len(expected_keys), zero_value=0.0)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1(precision, recall),
        "per_param": per_param,
    }


def score_completion(missing_params_by_turn, n_turns=DEFAULT_TURNS):
    turns = missing_params_by_turn or []
    max_turns = min(n_turns, len(turns)) if turns else n_turns
    for idx in range(max_turns):
        if not turns[idx]:
            return {"completed": True, "turns_used": idx + 1}
    return {"completed": False, "turns_used": max_turns}


def score_outline(expected_outline, actual_outline):
    expected_paths = flatten_outline_paths(expected_outline)
    actual_paths = flatten_outline_paths(actual_outline)

    correct = len(expected_paths & actual_paths)
    precision = safe_div(correct, len(actual_paths), zero_value=0.0)
    recall = safe_div(correct, len(expected_paths), zero_value=0.0)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1(precision, recall),
        "expected_nodes": len(expected_paths),
        "actual_nodes": len(actual_paths),
    }


def _compare_reported_vs_actual(reported_value, actual_value, tolerance=None):
    rep = normalize_fact_value(reported_value)
    act = normalize_fact_value(actual_value)
    if rep is None or act is None:
        return False
    if isinstance(rep, float) and isinstance(act, float):
        tol = tolerance if tolerance is not None else 0.0
        return abs(rep - act) <= tol
    if isinstance(rep, list) and isinstance(act, list):
        return set(rep) == set(act)
    return rep == act


def score_content_assertions(assertions, report_facts, adapter):
    results = []
    passes = 0
    fails = 0
    missing = 0
    errors = 0

    report_facts = report_facts or {}

    for assertion in assertions or []:
        statement_id = assertion.get("statement_id")
        sql = assertion.get("sql")
        tolerance = assertion.get("tolerance")
        expected_value = assertion.get("expected_value")
        expected_range = assertion.get("expected_range")

        try:
            actual_value = adapter.execute_scalar(sql)
        except Exception as exc:
            results.append(
                {
                    "statement_id": statement_id,
                    "status": "error",
                    "error": str(exc),
                }
            )
            errors += 1
            continue

        ground_truth_ok = True
        if expected_range and actual_value is not None:
            min_v = expected_range.get("min")
            max_v = expected_range.get("max")
            if min_v is not None and actual_value < min_v:
                ground_truth_ok = False
            if max_v is not None and actual_value > max_v:
                ground_truth_ok = False
        elif expected_value is not None:
            ground_truth_ok = _compare_reported_vs_actual(
                expected_value, actual_value, tolerance
            )

        reported_value = report_facts.get(statement_id)
        if reported_value is None:
            missing += 1
            results.append(
                {
                    "statement_id": statement_id,
                    "status": "missing",
                    "actual_value": actual_value,
                    "ground_truth_ok": ground_truth_ok,
                }
            )
            continue

        matched = _compare_reported_vs_actual(reported_value, actual_value, tolerance)
        if matched:
            passes += 1
            status = "pass"
        else:
            fails += 1
            status = "fail"

        results.append(
            {
                "statement_id": statement_id,
                "status": status,
                "actual_value": actual_value,
                "reported_value": reported_value,
                "ground_truth_ok": ground_truth_ok,
            }
        )

    total = len(assertions or [])
    return {
        "pass_rate": safe_div(passes, total, zero_value=0.0),
        "fail_rate": safe_div(fails, total, zero_value=0.0),
        "missing_rate": safe_div(missing, total, zero_value=0.0),
        "error_rate": safe_div(errors, total, zero_value=0.0),
        "results": results,
    }


def evaluate_report_case(case_payload, output_payload, adapter, config=None):
    config = config or {}
    n_turns = config.get("n_turns", DEFAULT_TURNS)

    template_metrics = score_template(
        expected_template_id=case_payload.get("expected_template_id"),
        predicted_template_id=output_payload.get("selected_template_id"),
        predicted_ranked_ids=output_payload.get("candidate_template_ids"),
        k=config.get("topk", 3),
    )

    params_metrics = score_params(
        case_payload.get("param_ground_truth"),
        output_payload.get("filled_params"),
    )

    missing_by_turn = output_payload.get("missing_params_by_turn")
    if missing_by_turn is None:
        turns = output_payload.get("turns") or []
        missing_by_turn = [turn.get("missing_params") for turn in turns]

    completion_metrics = score_completion(missing_by_turn, n_turns=n_turns)

    outline_metrics = score_outline(
        case_payload.get("outline_ground_truth"),
        output_payload.get("outline"),
    )

    report_json = output_payload.get("report_json") or {}
    report_facts = report_json.get("facts") or output_payload.get("report_facts")

    content_metrics = score_content_assertions(
        case_payload.get("content_assertions"),
        report_facts,
        adapter,
    )

    overall = (
        template_metrics["top1"]
        + params_metrics["f1"]
        + (1.0 if completion_metrics["completed"] else 0.0)
        + outline_metrics["f1"]
        + content_metrics["pass_rate"]
    ) / 5.0

    return {
        "template": template_metrics,
        "params": params_metrics,
        "completion": completion_metrics,
        "outline": outline_metrics,
        "content": content_metrics,
        "overall_score": overall,
    }
