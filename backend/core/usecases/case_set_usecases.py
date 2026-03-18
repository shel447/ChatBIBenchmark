from typing import Dict, List, Optional, Tuple

from backend.adapters.excel_case_set_adapter import export_case_set_workbook, parse_case_set_workbook
from backend.storage.case_set_repository import SqliteCaseSetRepository


def _case_set_to_dict(case_set) -> Dict[str, object]:
    return {
        "id": case_set.id,
        "name": case_set.name,
        "type": case_set.type,
        "description": case_set.description,
        "tags": case_set.tags,
        "is_seed": case_set.is_seed,
        "schema_version": case_set.schema_version,
        "created_at": case_set.created_at,
        "updated_at": case_set.updated_at,
    }


def _case_item_to_dict(case_item) -> Dict[str, object]:
    return {
        "id": case_item.id,
        "case_id": case_item.case_id,
        "title": case_item.title,
        "payload": case_item.payload,
    }


def list_case_sets(repo: SqliteCaseSetRepository) -> List[Dict[str, object]]:
    return [_case_set_to_dict(case_set) for case_set in repo.list_case_sets()]


def get_case_set_detail(repo: SqliteCaseSetRepository, case_set_id: str) -> Optional[Dict[str, object]]:
    case_set = repo.get_case_set(case_set_id)
    if not case_set:
        return None
    cases = repo.list_cases(case_set_id)
    return {
        "case_set": _case_set_to_dict(case_set),
        "cases": [_case_item_to_dict(case_item) for case_item in cases],
    }


def export_case_set(repo: SqliteCaseSetRepository, case_set_id: str) -> Optional[Tuple[str, bytes]]:
    detail = get_case_set_detail(repo, case_set_id)
    if not detail:
        return None
    workbook_bytes = export_case_set_workbook(
        detail["case_set"]["name"],
        detail["case_set"]["type"],
        detail["cases"],
    )
    filename = f"{detail['case_set']['name']}.xlsx"
    return filename, workbook_bytes


def import_case_set(repo: SqliteCaseSetRepository, case_set_id: str, content: bytes) -> Optional[Dict[str, object]]:
    case_set = repo.get_case_set(case_set_id)
    if not case_set:
        return None
    parsed_cases = parse_case_set_workbook(case_set.type, content)
    repo.replace_cases(case_set_id, parsed_cases)
    return get_case_set_detail(repo, case_set_id)
