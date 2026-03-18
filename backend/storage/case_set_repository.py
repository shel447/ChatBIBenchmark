import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from backend.core.domain.case_set import CaseItem, CaseSet


SCHEMA = """
create table if not exists case_set (
  id text primary key,
  name text not null,
  type text not null,
  description text not null,
  tags_json text not null,
  is_seed integer not null,
  schema_version text not null,
  created_at text not null,
  updated_at text not null
);

create table if not exists case_item (
  id text primary key,
  case_set_id text not null,
  case_id text not null,
  title text not null,
  payload_json text not null,
  created_at text not null,
  updated_at text not null
);
"""


SEEDED_CASE_SETS = [
    {
        "id": "cs-seed",
        "name": "零售 种子用例集",
        "type": "NL2SQL",
        "description": "不完整用例，用于扩增训练素材。",
        "tags": ["nl2sql", "seed"],
        "is_seed": True,
    },
    {
        "id": "cs-nl2sql",
        "name": "零售 NL2SQL 基准",
        "type": "NL2SQL",
        "description": "覆盖销量、GMV、客单价等核心指标问答。",
        "tags": ["nl2sql", "retail"],
        "is_seed": False,
    },
    {
        "id": "cs-nl2chart",
        "name": "零售 NL2CHART 基准",
        "type": "NL2CHART",
        "description": "重点评测图表类型匹配与指标选择。",
        "tags": ["nl2chart", "visual"],
        "is_seed": False,
    },
    {
        "id": "cs-smart-qa",
        "name": "智能问数 E2E",
        "type": "智能问数",
        "description": "SQL + 图表联合评测，覆盖端到端体验。",
        "tags": ["智能问数", "e2e"],
        "is_seed": False,
    },
    {
        "id": "cs-report",
        "name": "报告多轮交互",
        "type": "报告多轮交互",
        "description": "模板选择、参数收集与内容断言。",
        "tags": ["report", "multi-turn"],
        "is_seed": False,
    },
]


SEEDED_CASE_ITEMS = {
    "cs-nl2sql": [
        {
            "case_id": "NL2SQL-014",
            "title": "一月 GMV 汇总",
            "payload": {
                "case_id": "NL2SQL-014",
                "question": "统计一月 GMV 汇总。",
                "expected_sql": "SELECT SUM(gmv) FROM retail_sales WHERE month = '2026-01'",
            },
        },
        {
            "case_id": "NL2SQL-031",
            "title": "大区客单价对比",
            "payload": {
                "case_id": "NL2SQL-031",
                "question": "比较各大区客单价。",
                "expected_sql": "SELECT region, AVG(price) FROM retail_sales GROUP BY region",
            },
        },
    ],
    "cs-nl2chart": [
        {
            "case_id": "NL2CHART-011",
            "title": "月度订单趋势图",
            "payload": {
                "case_id": "NL2CHART-011",
                "question": "生成月度订单趋势图。",
                "sql": "SELECT month, SUM(orders) AS orders FROM retail_sales GROUP BY month",
                "expected_chart_type": "line",
            },
        }
    ],
    "cs-smart-qa": [
        {
            "case_id": "E2E-008",
            "title": "经营总览",
            "payload": {
                "case_id": "E2E-008",
                "question": "展示本月 GMV 趋势并给出趋势图。",
                "expected_sql": "SELECT day, SUM(gmv) AS gmv FROM retail_sales GROUP BY day",
                "expected_chart_type": "line",
            },
        }
    ],
    "cs-report": [
        {
            "case_id": "REPORT-002",
            "title": "一月经营报告",
            "payload": {
                "case_id": "REPORT-002",
                "user_goal": "生成一月经营报告",
                "template_name": "经营月报模板",
                "dialogue_script": [{"role": "user", "content": "生成一月经营报告"}],
                "param_ground_truth": {"date_range": "2026-01"},
                "outline_ground_truth": {"title": "经营概览", "children": []},
                "content_assertions": [{"statement": "GMV", "expected": 100}],
            },
        }
    ],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _case_set_from_row(row) -> CaseSet:
    return CaseSet(
        id=row[0],
        name=row[1],
        type=row[2],
        description=row[3],
        tags=json.loads(row[4] or "[]"),
        is_seed=bool(row[5]),
        schema_version=row[6],
        created_at=row[7],
        updated_at=row[8],
    )


def _case_item_from_row(row) -> CaseItem:
    return CaseItem(
        id=row[0],
        case_set_id=row[1],
        case_id=row[2],
        title=row[3],
        payload=json.loads(row[4] or "{}"),
        created_at=row[5],
        updated_at=row[6],
    )


def init_case_set_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        cur = conn.execute("select count(1) from case_set")
        if cur.fetchone()[0] == 0:
            _seed_case_sets(conn)
        conn.commit()
    finally:
        conn.close()


def _seed_case_sets(conn: sqlite3.Connection) -> None:
    now = _utc_now()
    for item in SEEDED_CASE_SETS:
        conn.execute(
            "insert into case_set(id, name, type, description, tags_json, is_seed, schema_version, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item["id"],
                item["name"],
                item["type"],
                item["description"],
                json.dumps(item["tags"], ensure_ascii=False),
                1 if item["is_seed"] else 0,
                "v1",
                now,
                now,
            ),
        )
    for case_set_id, cases in SEEDED_CASE_ITEMS.items():
        _insert_case_items(conn, case_set_id, cases)


def _insert_case_items(conn: sqlite3.Connection, case_set_id: str, cases: Iterable[dict]) -> None:
    now = _utc_now()
    for index, item in enumerate(cases, start=1):
        conn.execute(
            "insert into case_item(id, case_set_id, case_id, title, payload_json, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?)",
            (
                f"{case_set_id}-{index}",
                case_set_id,
                item["case_id"],
                item["title"],
                json.dumps(item["payload"], ensure_ascii=False),
                now,
                now,
            ),
        )


class SqliteCaseSetRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_case_sets(self) -> List[CaseSet]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "select id, name, type, description, tags_json, is_seed, schema_version, created_at, updated_at from case_set order by created_at asc"
            )
            return [_case_set_from_row(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_case_set(self, case_set_id: str) -> Optional[CaseSet]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "select id, name, type, description, tags_json, is_seed, schema_version, created_at, updated_at from case_set where id = ?",
                (case_set_id,),
            )
            row = cur.fetchone()
            return _case_set_from_row(row) if row else None
        finally:
            conn.close()

    def list_cases(self, case_set_id: str) -> List[CaseItem]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "select id, case_set_id, case_id, title, payload_json, created_at, updated_at from case_item where case_set_id = ? order by case_id asc",
                (case_set_id,),
            )
            return [_case_item_from_row(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def replace_cases(self, case_set_id: str, cases: List[dict]) -> List[CaseItem]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("delete from case_item where case_set_id = ?", (case_set_id,))
            _insert_case_items(conn, case_set_id, cases)
            conn.execute("update case_set set updated_at = ? where id = ?", (_utc_now(), case_set_id))
            conn.commit()
            cur = conn.execute(
                "select id, case_set_id, case_id, title, payload_json, created_at, updated_at from case_item where case_set_id = ? order by case_id asc",
                (case_set_id,),
            )
            return [_case_item_from_row(row) for row in cur.fetchall()]
        finally:
            conn.close()
