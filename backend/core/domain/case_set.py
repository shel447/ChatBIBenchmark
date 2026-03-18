from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CaseSet:
    id: str
    name: str
    type: str
    description: str
    tags: List[str]
    is_seed: bool
    schema_version: str
    created_at: str
    updated_at: str


@dataclass
class CaseItem:
    id: str
    case_set_id: str
    case_id: str
    title: str
    payload: Dict[str, Any]
    created_at: str
    updated_at: str
