# 评测任务进展与创建 API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在任务列表与任务详情展示进展/准确率，并新增评测任务创建 API（SQLite + DDD/整洁架构）。

**Architecture:** 新增 Run 领域实体与仓储端口，SQLite 仓储实现持久化；API 层仅调用用例层。前端仅做静态 UI 表达。

**Tech Stack:** FastAPI, SQLite, Vanilla HTML/CSS/JS, unittest

---

### Task 1: 新增 Run API 的失败测试

**Files:**
- Create: `tests/test_runs_api.py`

**Step 1: Write the failing test**

```python
import unittest
from fastapi.testclient import TestClient

from backend.app import app


class RunApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_list_get_run(self):
        payload = {
            "name": "零售 v1.4",
            "case_set_id": "cs-001",
            "environment_id": "env-001",
            "metric_set_id": "ms-001",
            "repeat_count": 2,
        }
        create_resp = self.client.post("/api/runs", json=payload)
        self.assertEqual(create_resp.status_code, 200)
        data = create_resp.json()
        self.assertIn("run", data)
        run = data["run"]
        self.assertEqual(run["case_set_id"], "cs-001")
        self.assertEqual(run["repeat_count"], 2)
        self.assertEqual(run["total_cases"], 0)
        self.assertEqual(run["executed_cases"], 0)
        self.assertEqual(run["accuracy"], 0)

        list_resp = self.client.get("/api/runs")
        self.assertEqual(list_resp.status_code, 200)
        runs = list_resp.json().get("runs", [])
        self.assertTrue(any(item["run_id"] == run["run_id"] for item in runs))

        detail_resp = self.client.get(f"/api/runs/{run['run_id']}")
        self.assertEqual(detail_resp.status_code, 200)
        detail = detail_resp.json()["run"]
        self.assertEqual(detail["environment_id"], "env-001")
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_runs_api.py -v`  
Expected: FAIL with 404 or missing route.

**Step 3: Commit**

```bash
git add tests/test_runs_api.py
git commit -m "test: add run api tests"
```

---

### Task 2: 实现 Run 领域模型与仓储端口（最小可用）

**Files:**
- Create: `backend/core/domain/run.py`
- Create: `backend/core/ports/run_repository.py`
- Create: `backend/core/usecases/run_usecases.py`

**Step 1: Write minimal implementation**

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class Run:
    run_id: str
    name: str
    case_set_id: str
    environment_id: str
    metric_set_id: str
    repeat_count: int
    total_cases: int
    executed_cases: int
    accuracy: float
    status: str
    started_at: str
    ended_at: Optional[str]
```

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.run import Run


class RunRepository(ABC):
    @abstractmethod
    def create(self, run: Run) -> Run:
        raise NotImplementedError

    @abstractmethod
    def list(self, limit: int = 50) -> List[Run]:
        raise NotImplementedError

    @abstractmethod
    def get(self, run_id: str) -> Optional[Run]:
        raise NotImplementedError
```

```python
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from ..domain.run import Run
from ..ports.run_repository import RunRepository


def create_run(
    repo: RunRepository,
    name: str,
    case_set_id: str,
    environment_id: str,
    metric_set_id: str,
    repeat_count: int,
) -> Run:
    run = Run(
        run_id=str(uuid.uuid4()),
        name=name,
        case_set_id=case_set_id,
        environment_id=environment_id,
        metric_set_id=metric_set_id,
        repeat_count=repeat_count,
        total_cases=0,
        executed_cases=0,
        accuracy=0,
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
        ended_at=None,
    )
    return repo.create(run)


def list_runs(repo: RunRepository, limit: int = 50) -> List[Run]:
    return repo.list(limit)


def get_run(repo: RunRepository, run_id: str) -> Optional[Run]:
    return repo.get(run_id)
```

**Step 2: Commit**

```bash
git add backend/core/domain/run.py backend/core/ports/run_repository.py backend/core/usecases/run_usecases.py
git commit -m "feat: add run domain and ports"
```

---

### Task 3: SQLite 仓储与数据库初始化

**Files:**
- Create: `backend/storage/run_repository.py`

**Step 1: Write minimal implementation**

```python
import sqlite3
from typing import List, Optional

from backend.core.domain.run import Run


SCHEMA = """
create table if not exists eval_run (
  run_id text primary key,
  name text not null,
  case_set_id text not null,
  environment_id text not null,
  metric_set_id text not null,
  repeat_count integer not null,
  total_cases integer not null,
  executed_cases integer not null,
  accuracy real not null,
  status text not null,
  started_at text not null,
  ended_at text
);
"""


def init_run_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


class SqliteRunRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, run: Run) -> Run:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "insert into eval_run(run_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, started_at, ended_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.run_id,
                    run.name,
                    run.case_set_id,
                    run.environment_id,
                    run.metric_set_id,
                    run.repeat_count,
                    run.total_cases,
                    run.executed_cases,
                    run.accuracy,
                    run.status,
                    run.started_at,
                    run.ended_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return run

    def list(self, limit: int = 50) -> List[Run]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, started_at, ended_at "
                "from eval_run order by started_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [
            Run(
                run_id=row[0],
                name=row[1],
                case_set_id=row[2],
                environment_id=row[3],
                metric_set_id=row[4],
                repeat_count=row[5],
                total_cases=row[6],
                executed_cases=row[7],
                accuracy=row[8],
                status=row[9],
                started_at=row[10],
                ended_at=row[11],
            )
            for row in rows
        ]

    def get(self, run_id: str) -> Optional[Run]:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, started_at, ended_at "
                "from eval_run where run_id = ?",
                (run_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        if not row:
            return None
        return Run(
            run_id=row[0],
            name=row[1],
            case_set_id=row[2],
            environment_id=row[3],
            metric_set_id=row[4],
            repeat_count=row[5],
            total_cases=row[6],
            executed_cases=row[7],
            accuracy=row[8],
            status=row[9],
            started_at=row[10],
            ended_at=row[11],
        )
```

**Step 2: Commit**

```bash
git add backend/storage/run_repository.py
git commit -m "feat: add sqlite run repository"
```

---

### Task 4: API 集成与测试转绿

**Files:**
- Modify: `backend/app.py`

**Step 1: Implement minimal API**

```python
from .core.usecases.run_usecases import create_run, get_run, list_runs
from .storage.run_repository import SqliteRunRepository, init_run_db

DEFAULT_RUN_DB = os.path.join(APP_DIR, "runs.db")

@app.on_event("startup")
async def _startup():
    init_db(DEFAULT_META_DB)
    init_run_db(DEFAULT_RUN_DB)

@app.post("/api/runs")
async def create_run_api(request: Request):
    payload = await request.json()
    for key in ("name", "case_set_id", "environment_id", "metric_set_id", "repeat_count"):
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"{key} is required")
    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    run = create_run(
        repo,
        payload["name"],
        payload["case_set_id"],
        payload["environment_id"],
        payload["metric_set_id"],
        payload["repeat_count"],
    )
    return {"run": run.__dict__}

@app.get("/api/runs")
async def list_runs_api():
    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    runs = [run.__dict__ for run in list_runs(repo)]
    return {"runs": runs}

@app.get("/api/runs/{run_id}")
async def get_run_api(run_id: str):
    repo = SqliteRunRepository(DEFAULT_RUN_DB)
    run = get_run(repo, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run": run.__dict__}
```

**Step 2: Run test to verify it passes**

Run: `python -m unittest tests/test_runs_api.py -v`  
Expected: PASS.

**Step 3: Commit**

```bash
git add backend/app.py
git commit -m "feat: add run api endpoints"
```

---

### Task 5: 前端路由测试更新（先红）

**Files:**
- Modify: `tests/test_frontend_routes.py`

**Step 1: Write failing assertions**

```python
self.assertIn("进展", body)
self.assertIn("准确率", body)
self.assertIn("用例集执行次数", body)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: FAIL with missing strings.

**Step 3: Commit**

```bash
git add tests/test_frontend_routes.py
git commit -m "test: assert run progress UI strings"
```

---

### Task 6: 前端任务列表展示进展与准确率

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`

**Step 1: Update HTML**

- 表头改为：`任务 / 用例集 / 环境 / 启动时间 / 结束时间 / 指标参数集 / 进展 / 准确率`
- 表格行新增示例值（如 `60/200`、`87%`）。
- 移除模板 Top1/参数 F1/完成率/内容通过/得分列。

**Step 2: Update CSS**

- 新增 `progress` 与 `accuracy` 文案样式（如需要）。

**Step 3: Commit**

```bash
git add frontend/index.html frontend/styles.css
git commit -m "ui: show run progress and accuracy in list"
```

---

### Task 7: 任务详情增加进展/准确率与执行次数配置

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`

**Step 1: Update HTML**

- 任务详情指标区只保留：`进展`、`准确率`。
- 新增“配置”区块，包含 `用例集执行次数` 输入框或下拉。
- “已执行分析结果”区域仅展示准确率（可与指标区复用）。

**Step 2: Update CSS**

- 新增配置区块样式，保持与现有面板一致。

**Step 3: Run test to verify it passes**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: PASS.

**Step 4: Commit**

```bash
git add frontend/index.html frontend/styles.css
git commit -m "ui: add run detail progress and repeat config"
```

---

### Task 8: 全量回归

**Files:**
- None

**Step 1: Run all tests**

Run: `python -m unittest -v`  
Expected: PASS (may include existing deprecation warnings).

**Step 2: Commit**

```bash
git status -sb
```

