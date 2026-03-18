import hashlib
from datetime import datetime, timezone
from statistics import mean
from typing import Dict, List, Optional

from backend.core.domain.run_case_result import RunCaseResult
from backend.storage.case_set_repository import SqliteCaseSetRepository
from backend.storage.run_repository import SqliteRunRepository, SqliteTaskRepository


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:8], 16)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, round(value, 4)))


def _case_type_key(case_set_type: str) -> str:
    return case_set_type or "通用"


def _issue_tags(case_set_type: str, accuracy: float, variant: int) -> List[str]:
    if accuracy >= 0.86:
        return ["稳定通过"]
    if case_set_type == "NL2SQL":
        return ["结果不一致", "聚合偏差"] if variant % 2 == 0 else ["可执行但结果偏差"]
    if case_set_type == "NL2CHART":
        return ["图表类型偏差", "字段绑定缺失"] if variant % 2 == 0 else ["渲染结构不稳定"]
    if case_set_type == "智能问数":
        return ["SQL 与图表不一致", "摘要偏差"] if variant % 2 == 0 else ["图表表达失真"]
    if case_set_type == "报告多轮交互":
        return ["参数收集不完整", "内容事实波动"] if variant % 2 == 0 else ["模板选择偏差"]
    return ["结果波动"]


def _detail_metrics(case_set_type: str, accuracy: float, variant: int) -> Dict[str, float]:
    if case_set_type == "NL2SQL":
        return {
            "execution_accuracy": _clamp(accuracy),
            "test_suite_accuracy": _clamp(accuracy - 0.03),
            "executable_rate": _clamp(accuracy + 0.08),
            "result_stability": _clamp(0.82 + (variant % 5) * 0.03),
        }
    if case_set_type == "NL2CHART":
        return {
            "render_success_rate": _clamp(accuracy + 0.06),
            "chart_type_accuracy": _clamp(accuracy - 0.02),
            "field_binding_f1": _clamp(accuracy - 0.05),
            "chart_fidelity_score": _clamp(accuracy + 0.01),
        }
    if case_set_type == "智能问数":
        return {
            "sql_result_accuracy": _clamp(accuracy - 0.03),
            "chart_type_accuracy": _clamp(accuracy - 0.01),
            "answer_consistency": _clamp(accuracy + 0.02),
        }
    if case_set_type == "报告多轮交互":
        return {
            "template_top1_accuracy": _clamp(accuracy + 0.04),
            "param_slot_f1": _clamp(accuracy - 0.03),
            "outline_structure_f1": _clamp(accuracy - 0.02),
            "factual_precision": _clamp(accuracy + 0.01),
        }
    return {"accuracy": _clamp(accuracy)}


def _status_label(accuracy: float) -> str:
    if accuracy >= 0.86:
        return "通过"
    if accuracy >= 0.72:
        return "波动"
    return "失败"


def _summary(case_title: str, case_set_type: str, accuracy: float, tags: List[str]) -> str:
    return f"{case_title} 在 {case_set_type} 评测中准确率 {round(accuracy * 100)}%，关注：{'、'.join(tags)}。"


def _accuracy_for_case(case_item: dict, case_set_type: str, metric_set_id: str, environment_id: str, run_index: int) -> float:
    seed = _stable_int(f"{case_item['case_id']}:{metric_set_id}:{environment_id}")
    cohort = seed % 4
    base = 0.68 + ((seed >> 3) % 20) / 100
    environment_shift = 0.02 if environment_id == "env-staging" else -0.01
    metric_shift = -0.03 if metric_set_id in {"metric-strict", "metric-report-dialogue"} else 0.01
    progression = 0.015 * min(run_index - 1, 2)
    last_digit = int(case_item["case_id"][-1]) if case_item["case_id"][-1].isdigit() else seed % 10
    regression = -0.09 if (last_digit % 2 == 0 and run_index >= 2) else 0.0
    if cohort == 0 and run_index >= 3:
        regression -= 0.05
    elif cohort == 1 and run_index >= 2:
        regression += 0.05
    elif cohort == 2:
        regression += ((run_index + seed) % 3 - 1) * 0.025
    else:
        regression -= 0.02 if run_index % 2 == 0 else 0.0
    type_shift = {
        "NL2SQL": 0.0,
        "NL2CHART": -0.01,
        "智能问数": -0.015,
        "报告多轮交互": -0.02,
    }.get(case_set_type, 0.0)
    return _clamp(base + environment_shift + metric_shift + progression + regression + type_shift, 0.42, 0.98)


def materialize_execution_results(
    run_repo: SqliteRunRepository,
    task_repo: SqliteTaskRepository,
    case_set_repo: SqliteCaseSetRepository,
    run_id: str,
) -> Optional[dict]:
    run = run_repo.get(run_id)
    if not run:
        return None
    case_set = case_set_repo.get_case_set(run.case_set_id)
    if not case_set:
        run.execution_status = "succeeded"
        run.ended_at = _utc_now()
        run_repo.update(run)
        return {"run": run, "case_results": []}

    cases = case_set_repo.list_cases(run.case_set_id)
    historical_runs = [
        item
        for item in run_repo.list_by_case_set(run.case_set_id, limit=200)
        if item.environment_id == run.environment_id and item.started_at <= run.started_at
    ]
    run_index = max(1, len(historical_runs))
    now = _utc_now()
    results: List[RunCaseResult] = []
    for case_item in cases:
        accuracy = _accuracy_for_case(
            {"case_id": case_item.case_id, "title": case_item.title, "payload": case_item.payload},
            case_set.type,
            run.metric_set_id,
            run.environment_id,
            run_index,
        )
        variant = _stable_int(f"{run_id}:{case_item.case_id}")
        tags = _issue_tags(case_set.type, accuracy, variant)
        detail_metrics = _detail_metrics(case_set.type, accuracy, variant)
        results.append(
            RunCaseResult(
                run_id=run.run_id,
                task_id=run.task_id,
                case_set_id=run.case_set_id,
                case_id=case_item.case_id,
                case_title=case_item.title,
                case_type=_case_type_key(case_set.type),
                accuracy=accuracy,
                status=_status_label(accuracy),
                issue_tags=tags,
                detail_metrics=detail_metrics,
                summary=_summary(case_item.title, case_set.type, accuracy, tags),
                created_at=now,
                updated_at=now,
            )
        )

    run.total_cases = len(results)
    run.executed_cases = len(results)
    run.accuracy = _clamp(mean(item.accuracy for item in results)) if results else 0.0
    run.execution_status = "succeeded"
    run.ended_at = now
    run_repo.update(run)
    run_repo.replace_case_results(run.run_id, results)

    if run.task_id:
        task = task_repo.get(run.task_id)
        if task:
            task.task_status = "succeeded"
            task.latest_execution_id = run.run_id
            task.updated_at = now
            task_repo.update(task)

    return {"run": run, "case_results": results}

