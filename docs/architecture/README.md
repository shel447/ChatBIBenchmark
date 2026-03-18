# ChatBIBenchmark 设计文档索引

## 1. 文档目的

本文档索引用于组织 ChatBIBenchmark 当前实现对应的设计基线。设计文档以当前代码为准，覆盖整体架构、核心模块设计、数据存储与部署视图。后续功能变更时，必须同步更新对应设计文档与图示。

## 2. 阅读顺序

| 顺序 | 文档 | 目的 |
| --- | --- | --- |
| 1 | [01-overall-architecture.md](./01-overall-architecture.md) | 解释系统整体边界、模块配合关系与 4+1 视图 |
| 2 | [02-backend-application-and-api.md](./02-backend-application-and-api.md) | 解释 FastAPI 应用装配、API 分组与分层依赖 |
| 3 | [03-case-set-management.md](./03-case-set-management.md) | 解释用例集、用例、Excel 导入导出与种子用例集 |
| 4 | [04-task-execution-and-scheduling.md](./04-task-execution-and-scheduling.md) | 解释评测任务、执行记录、定时任务与状态流转 |
| 5 | [05-metric-management.md](./05-metric-management.md) | 解释指标参数集、执行映射、生效状态与管理方式 |
| 6 | [06-report-evaluation-engine.md](./06-report-evaluation-engine.md) | 解释报告多轮交互评测引擎、评分公式与 run 汇总 |
| 7 | [07-frontend-console.md](./07-frontend-console.md) | 解释前端单页控制台的页面组织、状态与交互 |
| 8 | [08-storage-and-deployment.md](./08-storage-and-deployment.md) | 解释 SQLite 拆分存储、部署形态、运行边界与持久化建议 |

## 3. 代码映射

| 模块 | 主要代码目录 | 说明 |
| --- | --- | --- |
| 后端应用装配 | `backend/app.py` | 路由、静态资源挂载、启动初始化、调度线程 |
| 领域与用例 | `backend/core/domain` `backend/core/usecases` `backend/core/ports` | DDD 风格的实体、端口、应用服务 |
| 存储实现 | `backend/storage` | SQLite 仓储与报告评测持久化 |
| 数据适配层 | `backend/adapters` | SQLite 查询适配器、Excel 用例导入导出 |
| 前端控制台 | `frontend/index.html` `frontend/app.js` `frontend/styles.css` | 单页应用的布局、逻辑与样式 |
| 测试 | `tests` | API、前端路由、报告评测和仓储测试 |

## 4. 当前实现边界

- 已实现真实后端能力：
  - 用例集查询、单个用例集 Excel 导入覆盖、单个与多选导出
  - 评测任务创建、待执行/立即执行区分、执行记录查询
  - 定时任务创建、查询、更新、删除与服务内轮询触发
  - 指标参数集管理与报告多轮交互指标真实生效
  - 报告评测原始评分、指标聚合评分、run 持久化与查询
- 当前仍为占位或静态展示的能力：
  - 环境配置页面尚未接入真实后端
  - 用例工具中的“扩增用例集”和“泛化规则管理”尚未接入真实后端
  - 顶部“导入用例”按钮未形成独立后端导入流程
  - `NL2SQL`、`NL2CHART`、`智能问数` 的指标集仍为“仅配置”，未接入真实执行链路

## 5. 文档维护规则

系统后续发生以下变化时，必须同步修改本文档包：

1. 新增或删除 API 路由。
2. 新增或修改领域实体、状态机、数据库表。
3. 指标集新增真实执行场景，或报告评测公式改变。
4. 用例集模型、Excel 模板、导入导出规则发生变化。
5. 前端新增一级页面、主要交互路径或状态管理方式发生变化。
6. 部署形态、数据库路径策略、持久化方式发生变化。

## 6. 变更建议

- 功能开发时，优先更新对应模块文档，再更新整体设计中的逻辑视图、过程视图和物理视图。
- 设计评审时，先检查本文档索引中的“当前实现边界”是否仍然成立。
- 当某个模块从“占位”转为“真实能力”时，应同时更新文档中的边界描述、时序图和接口清单。
