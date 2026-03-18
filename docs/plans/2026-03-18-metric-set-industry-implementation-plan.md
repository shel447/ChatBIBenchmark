# Metric Set Industry Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将“指标管理”从静态占位改造成可配置、可被任务真实关联的评测指标参数集，并内置面向 `NL2SQL`、`NL2CHART`、`报告多轮交互` 的业界化指标模板。

**Architecture:** 在 `runs.db` 中新增 `metric_set` 配置实体，采用“参数集 + 指标维度 JSON”存储模式；后端提供 `GET/POST/PATCH` API，前端“指标管理”页改为“列表 + 详情 + 编辑弹窗”结构，任务创建与详情改为消费真实指标集元数据。指标定义参考 `Spider/BIRD`、`Text2Vis/Chart2Code`、`MultiWOZ/FActScore` 的公开评测方法，但在产品内落地为可配置阈值、权重和硬门禁规则。

**Tech Stack:** FastAPI, SQLite, vanilla JS, HTML/CSS, unittest

---

### Task 1: 为 metric set 写失败测试

**Files:**
- Create: `tests/test_metric_sets_api.py`
- Modify: `tests/test_frontend_routes.py`

**Step 1: Write the failing test**

添加后端测试覆盖：
- `GET /api/metric-sets` 返回内置指标集
- `GET /api/metric-sets/{id}` 返回维度详情
- `POST /api/metric-sets` 可创建自定义参数集
- `PATCH /api/metric-sets/{id}` 可更新权重/阈值
- `POST /api/tasks` 使用不存在的 `metric_set_id` 返回 400

并在前端路由测试中加入关键文案断言：
- `执行准确率`
- `测试套件准确率`
- `图表类型准确率`
- `任务成功率`
- `事实精度`

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_metric_sets_api.py tests/test_frontend_routes.py -v`

Expected: `404` / `AttributeError` / 文案缺失，说明 API 与 UI 尚未实现。

### Task 2: 增加 metric set 领域模型、仓储与种子数据

**Files:**
- Create: `backend/core/domain/metric_set.py`
- Create: `backend/core/ports/metric_set_repository.py`
- Create: `backend/core/usecases/metric_set_usecases.py`
- Modify: `backend/storage/run_repository.py`

**Step 1: Write minimal domain model**

新增 `MetricSet` dataclass，字段至少包含：
- `metric_set_id`
- `name`
- `scenario_type`
- `description`
- `score_formula`
- `pass_threshold`
- `dimensions`
- `benchmark_refs`
- `created_at`
- `updated_at`

**Step 2: Extend SQLite schema**

在 `runs.db` 中新增 `metric_set` 表，字段包括：
- `metric_set_id`
- `name`
- `scenario_type`
- `description`
- `score_formula`
- `pass_threshold`
- `dimensions_json`
- `benchmark_refs_json`
- `created_at`
- `updated_at`

**Step 3: Seed practical metric sets**

内置至少 5 组：
- `metric-default`：ChatBI 通用发布基线
- `metric-strict`：ChatBI 严格发布门禁
- `metric-nl2sql-exec`：NL2SQL 执行可靠性
- `metric-nl2chart-fidelity`：NL2CHART 图表保真
- `metric-report-dialogue`：报告多轮交互生成

### Task 3: 增加 metric set API 与任务校验

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/core/usecases/task_usecases.py`（仅在必要时）

**Step 1: Add API**

新增：
- `GET /api/metric-sets`
- `GET /api/metric-sets/{metric_set_id}`
- `POST /api/metric-sets`
- `PATCH /api/metric-sets/{metric_set_id}`

**Step 2: Validate task creation**

在：
- `POST /api/tasks`
- `POST /api/runs`

中校验 `metric_set_id` 存在，否则返回 `400`。

**Step 3: Expose metric set summary in task payload**

任务列表/详情返回：
- `metric_set: { metric_set_id, name, scenario_type }`

### Task 4: 重构“指标管理”前端页面

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

**Step 1: Replace static table**

改为：
- 顶部概览卡：参数集数量、内置门禁数、覆盖任务类型
- 场景筛选：`全部 / NL2SQL / NL2CHART / 报告多轮交互 / 通用`
- 左侧参数集列表
- 右侧详情面板

**Step 2: Add detail panel**

详情中展示：
- 参数集名称、适用场景、总分公式、发布门槛
- 业界参考来源（标题 + 链接）
- 指标维度表：`指标名 / 度量方式 / 权重 / 合格阈值 / 硬门禁 / 业务意义`

**Step 3: Add create/edit modal**

支持编辑：
- 名称
- 说明
- 发布门槛
- 每个指标维度的 `weight / target / hard_gate`

### Task 5: 让任务创建与详情消费真实 metric set

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/index.html`

**Step 1: Load metric sets**

页面初始化时拉取 `/api/metric-sets`。

**Step 2: Populate task modal**

任务创建弹窗的“指标参数集”下拉改为真实数据。

**Step 3: Render metric set names**

任务列表与任务详情显示指标集名称而不是裸 ID。

### Task 6: 完整回归与收尾

**Files:**
- Test: `tests/test_metric_sets_api.py`
- Test: `tests/test_tasks_schedules_api.py`
- Test: `tests/test_frontend_routes.py`

**Step 1: Run focused tests**

Run:
- `python -m unittest tests/test_metric_sets_api.py -v`
- `python -m unittest tests/test_tasks_schedules_api.py -v`
- `python -m unittest tests/test_frontend_routes.py -v`

**Step 2: Run full regression**

Run:
- `python -m unittest tests/test_frontend_routes.py tests/test_case_sets_api.py tests/test_runs_api.py tests/test_tasks_schedules_api.py tests/test_metric_sets_api.py -v`
- `node --check frontend\\app.js`

**Step 3: Browser smoke test**

验证：
- “指标管理”页能展示行业化指标集
- 任务创建能选真实指标集
- 任务列表/详情显示指标集名称

