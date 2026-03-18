from statistics import mean, pstdev
from typing import Dict, List, Optional

from backend.storage.case_set_repository import SqliteCaseSetRepository
from backend.storage.run_repository import SqliteRunRepository


def _round(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(value, 4)


def _series_point(run) -> Dict[str, object]:
    return {
        "run_id": run.run_id,
        "task_id": run.task_id,
        "started_at": run.started_at,
        "accuracy": _round(run.accuracy),
        "environment_id": run.environment_id,
        "metric_set_id": run.metric_set_id,
        "execution_status": run.execution_status,
    }


def _build_case_map(run_repo: SqliteRunRepository, run_id: str) -> Dict[str, object]:
    return {item.case_id: item for item in run_repo.list_case_results(run_id)}


def _latest_delta(series: List[Dict[str, object]]) -> Optional[float]:
    if len(series) < 2:
        return None
    return _round(series[-1]["accuracy"] - series[-2]["accuracy"])


def get_case_set_trends(case_set_repo: SqliteCaseSetRepository, run_repo: SqliteRunRepository, case_set_id: str) -> Optional[Dict[str, object]]:
    case_set = case_set_repo.get_case_set(case_set_id)
    if not case_set:
        return None
    runs = [item for item in run_repo.list_by_case_set(case_set_id, limit=200) if item.total_cases > 0]
    series = [_series_point(item) for item in runs]
    regression_alerts = []
    improving_cases = []
    unstable_cases = []

    if len(runs) >= 2:
        all_regressions = []
        all_improvements = []
        for index in range(1, len(runs)):
            latest_map = _build_case_map(run_repo, runs[index].run_id)
            previous_map = _build_case_map(run_repo, runs[index - 1].run_id)
            shared_case_ids = sorted(set(latest_map.keys()) & set(previous_map.keys()))
            for case_id in shared_case_ids:
                latest = latest_map[case_id]
                previous = previous_map[case_id]
                delta = latest.accuracy - previous.accuracy
                item = {
                    "case_id": case_id,
                    "title": latest.case_title,
                    "latest_accuracy": _round(latest.accuracy),
                    "previous_accuracy": _round(previous.accuracy),
                    "delta": _round(delta),
                    "issue_tags": latest.issue_tags,
                    "from_run_id": runs[index - 1].run_id,
                    "to_run_id": runs[index].run_id,
                }
                if delta < 0:
                    all_regressions.append(item)
                elif delta > 0:
                    all_improvements.append(item)
        regression_alerts.extend(sorted(all_regressions, key=lambda item: item["delta"])[:8])
        improving_cases.extend(sorted(all_improvements, key=lambda item: item["delta"], reverse=True)[:8])
    for case_item in case_set_repo.list_cases(case_set_id):
        history = run_repo.list_case_history(case_set_id, case_item.case_id, limit=50)
        if len(history) < 2:
            continue
        accuracies = [item.accuracy for item in history]
        volatility = pstdev(accuracies)
        if volatility >= 0.05:
            unstable_cases.append(
                {
                    "case_id": case_item.case_id,
                    "title": case_item.title,
                    "volatility": _round(volatility),
                    "avg_accuracy": _round(mean(accuracies)),
                }
            )

    return {
        "case_set": {
            "id": case_set.id,
            "name": case_set.name,
            "type": case_set.type,
        },
        "summary": {
            "run_count": len(series),
            "avg_accuracy": _round(mean(item["accuracy"] for item in series)) if series else None,
            "latest_accuracy": series[-1]["accuracy"] if series else None,
            "latest_delta": _latest_delta(series),
        },
        "run_series": series,
        "regression_alerts": regression_alerts[:8],
        "improving_cases": improving_cases[:8],
        "unstable_cases": sorted(unstable_cases, key=lambda item: item["volatility"], reverse=True)[:8],
    }


def get_case_trends(case_set_repo: SqliteCaseSetRepository, run_repo: SqliteRunRepository, case_set_id: str, case_id: str) -> Optional[Dict[str, object]]:
    case_set = case_set_repo.get_case_set(case_set_id)
    if not case_set:
        return None
    case_item = next((item for item in case_set_repo.list_cases(case_set_id) if item.case_id == case_id), None)
    if not case_item:
        return None
    history = run_repo.list_case_history(case_set_id, case_id, limit=100)
    accuracy_series = [
        {
            "run_id": item.run_id,
            "task_id": item.task_id,
            "started_at": item.created_at,
            "accuracy": _round(item.accuracy),
            "status": item.status,
            "issue_tags": item.issue_tags,
        }
        for item in history
    ]
    accuracies = [item["accuracy"] for item in accuracy_series]
    return {
        "case_set": {
            "id": case_set.id,
            "name": case_set.name,
            "type": case_set.type,
        },
        "case_id": case_item.case_id,
        "title": case_item.title,
        "summary": {
            "run_count": len(accuracy_series),
            "avg_accuracy": _round(mean(accuracies)) if accuracies else None,
            "latest_accuracy": accuracies[-1] if accuracies else None,
            "latest_delta": _latest_delta(accuracy_series),
            "min_accuracy": min(accuracies) if accuracies else None,
            "max_accuracy": max(accuracies) if accuracies else None,
            "volatility": _round(pstdev(accuracies)) if len(accuracies) >= 2 else 0.0,
        },
        "accuracy_series": accuracy_series,
    }


def get_overview_analytics(case_set_repo: SqliteCaseSetRepository, run_repo: SqliteRunRepository) -> Dict[str, object]:
    case_set_summaries = []
    regression_alerts = []
    global_points = []

    for case_set in case_set_repo.list_case_sets():
        if case_set.is_seed:
            continue
        detail = get_case_set_trends(case_set_repo, run_repo, case_set.id)
        if not detail:
            continue
        summary = detail["summary"]
        case_set_summaries.append(
            {
                "case_set_id": case_set.id,
                "case_set_name": case_set.name,
                "type": case_set.type,
                "run_count": summary["run_count"],
                "latest_accuracy": summary["latest_accuracy"],
                "latest_delta": summary["latest_delta"],
                "avg_accuracy": summary["avg_accuracy"],
            }
        )
        regression_alerts.extend(
            {
                **item,
                "case_set_id": case_set.id,
                "case_set_name": case_set.name,
            }
            for item in detail["regression_alerts"]
        )
        for point in detail["run_series"]:
            global_points.append(
                {
                    "case_set_id": case_set.id,
                    "case_set_name": case_set.name,
                    **point,
                }
            )

    global_points.sort(key=lambda item: item["started_at"])
    global_accuracy_series = []
    by_timestamp = {}
    for point in global_points:
        by_timestamp.setdefault(point["started_at"], []).append(point["accuracy"])
    for started_at, accuracies in by_timestamp.items():
        global_accuracy_series.append({"started_at": started_at, "accuracy": _round(mean(accuracies))})

    return {
        "global_accuracy_series": global_accuracy_series,
        "case_set_summaries": sorted(case_set_summaries, key=lambda item: (item["latest_accuracy"] is None, item["latest_accuracy"])),
        "regression_alerts": sorted(regression_alerts, key=lambda item: item["delta"])[:10],
    }


