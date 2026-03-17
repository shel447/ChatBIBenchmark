# 评测任务进展与创建 API 设计

## 背景
评测任务列表与任务详情需要可见进展与准确率，并支持配置“用例集执行次数”。同时新增评测的服务端创建功能需落地，后端遵循 DDD/整洁架构，存储暂用 SQLite。

## 目标
- 任务列表与任务详情展示评测进展（总用例/已执行）与准确率（百分比）。
- 任务详情提供“用例集执行次数”配置入口（静态 UI）。
- 新增评测服务端 API：创建评测任务并持久化。
- 采用轻量 DDD/整洁架构分层，数据落 SQLite。

## 非目标
- 不实现真实调度、执行引擎或进度推进逻辑。
- 不实现前端真实排序/过滤逻辑，仅静态 UI 表达。
- 不实现环境/用例集/指标参数真实表，仅记录它们的 ID。

## 架构与组件
### 领域层
- `Run` 实体：描述评测任务的核心状态。

### 端口层
- `RunRepository`：抽象仓储接口。

### 用例层
- `create_run`：创建任务并落库。
- `list_runs`：列出任务。
- `get_run`：获取任务详情。

### 基础设施层
- SQLite 实现 `RunRepository`。
- 数据表 `eval_run` 持久化任务。

### API 层
- `POST /api/runs`：创建任务。
- `GET /api/runs`：列出任务。
- `GET /api/runs/{run_id}`：任务详情。

## 数据模型
### Run
字段（最小可用）：
- `run_id`：任务 ID
- `name`：任务名称
- `case_set_id`：用例集 ID
- `environment_id`：环境 ID
- `metric_set_id`：指标参数集 ID
- `repeat_count`：用例集执行次数
- `total_cases`：总用例数
- `executed_cases`：已执行用例数
- `accuracy`：准确率（0-1）
- `status`：running/completed/failed
- `started_at`：启动时间
- `ended_at`：结束时间

创建时默认：
- `total_cases=0`
- `executed_cases=0`
- `accuracy=0`
- `status=running`
- `started_at=now`
- `ended_at=null`

## API 设计
### POST /api/runs
请求：
```
{
  "name": "零售 v1.4",
  "case_set_id": "cs-001",
  "environment_id": "env-001",
  "metric_set_id": "ms-001",
  "repeat_count": 1
}
```
响应：返回 `run_id` 与完整字段（含默认值）。

### GET /api/runs
返回：
```
{ "runs": [Run, ...] }
```

### GET /api/runs/{run_id}
返回：
```
{ "run": Run }
```

## 前端 UI 调整
### 任务列表
- 列新增：`进展`、`准确率`。
- 移除模板 Top1/参数 F1/完成率/内容通过/得分列。
- 进展示例：`60/200`，准确率示例：`87%`。

### 任务详情
- 指标区仅展示：`进展`、`准确率`。
- 新增“配置”区块，包含 `用例集执行次数` 输入（静态）。
- 已执行部分的分析结果仅显示准确率。

## 数据流
1. 前端点击“新增评测” → 调用 `POST /api/runs`。
2. 后端创建 Run，填充默认进度与准确率。
3. 前端在列表与详情展示返回数据（本次静态 UI）。

## 错误处理
- 参数缺失：返回 400 + 错误信息。
- run_id 不存在：返回 404。

## 测试计划
- API：创建/列表/详情端点单元测试（TDD）。
- 前端：页面文案断言（进展、准确率、用例集执行次数）。

