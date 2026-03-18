# Architecture Document Pack Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于当前代码实现，为 ChatBIBenchmark 补齐一套可维护的设计文档包，覆盖整体架构设计和核心模块设计，明确模块协作关系、核心实现架构、持久化边界、运行流程与部署视图，并要求后续功能变更同步更新文档。

**Architecture:** 采用“总览文档 + 模块设计文档 + 索引文档”的文档结构。总览文档重点使用 4+1 视图解释系统上下文、逻辑拆分、运行流程、开发视图和部署视图；模块文档聚焦各模块的领域对象、端口/仓储、关键流程和核心时序。所有图统一使用 Mermaid 表达 UML/架构视图，文档与当前 FastAPI + SQLite + Vanilla JS 实现保持一致。

**Tech Stack:** Markdown, Mermaid, FastAPI, SQLite, vanilla JS

---

### Task 1: 盘点当前实现并定义文档结构

**Files:**
- Read: `backend/app.py`
- Read: `backend/core/**/*.py`
- Read: `backend/storage/**/*.py`
- Read: `frontend/index.html`
- Read: `frontend/app.js`
- Create: `docs/architecture/README.md`

**Step 1: Confirm module boundaries**

梳理并固定当前系统的核心模块：
- 前端控制台
- 后端 API 与应用装配
- 用例集管理
- 评测任务/执行记录/定时任务
- 指标管理
- 报告多轮交互评测引擎
- 数据存储与部署

**Step 2: Define document pack**

规划文档目录与命名，至少包含：
- 架构索引
- 整体架构设计
- 后端应用与接口设计
- 用例集与数据管理设计
- 评测任务、执行与调度设计
- 指标管理与评测配置设计
- 报告评测引擎设计
- 前端控制台设计
- 数据存储与部署设计

### Task 2: 编写整体架构设计文档

**Files:**
- Create: `docs/architecture/01-overall-architecture.md`

**Step 1: Cover 4+1 views**

在整体设计中至少覆盖：
- 场景/用例视图：主要用户与核心业务闭环
- 逻辑视图：模块关系、边界、职责
- 过程视图：任务创建、定时触发、报告评测等关键时序
- 开发视图：代码目录、分层、依赖方向
- 物理视图：运行节点、数据库文件、浏览器/服务部署关系

**Step 2: Explain module collaboration**

明确说明：
- 前端如何调用后端模块
- 任务与执行记录如何解耦
- 指标集如何参与报告评测聚合
- 调度器如何触发执行记录
- 多个 SQLite 库的职责边界

### Task 3: 编写各模块设计文档

**Files:**
- Create: `docs/architecture/02-backend-application-and-api.md`
- Create: `docs/architecture/03-case-set-management.md`
- Create: `docs/architecture/04-task-execution-and-scheduling.md`
- Create: `docs/architecture/05-metric-management.md`
- Create: `docs/architecture/06-report-evaluation-engine.md`
- Create: `docs/architecture/07-frontend-console.md`
- Create: `docs/architecture/08-storage-and-deployment.md`

**Step 1: Backend application and API**

说明 FastAPI 应用装配、路由组织、依赖注入方式、启动初始化与调度线程。

**Step 2: Case set module**

说明用例集/用例通用模型、类型扩展 payload、Excel 导入导出与种子用例集机制。

**Step 3: Task execution and scheduling**

说明 `Task / Execution / ScheduleJob` 三层模型、状态机、运行摘要、手动/定时触发链路。

**Step 4: Metric management**

说明 `metric_set` 结构、维度定义、激活状态、与任务/报告评测的关联边界。

**Step 5: Report evaluation**

说明原始评测、指标映射、加权评分、硬门禁、run 汇总与持久化。

**Step 6: Frontend console**

说明单页前端的视图组织、页面切换、数据加载模式和关键交互。

**Step 7: Storage and deployment**

说明 `runs.db / case_sets.db / report_eval.db` 的拆分原因、表职责、部署与持久化建议。

### Task 4: 增加索引与变更维护约束

**Files:**
- Create: `docs/architecture/README.md`

**Step 1: Add reading order**

提供文档导航、阅读顺序、文档与代码目录映射。

**Step 2: Add maintenance rule**

明确要求：
- 功能变更必须同步更新对应设计文档
- 数据模型、API、关键流程变化时必须更新整体设计中的相关视图

### Task 5: 校验文档一致性

**Files:**
- Verify: `docs/architecture/*.md`

**Step 1: Structural verification**

检查：
- 文档链接是否可用
- Mermaid 代码块格式是否正确
- 文件命名和章节结构是否统一

**Step 2: Consistency verification**

对照当前代码确认：
- API 路由与文档一致
- 领域模型命名与文档一致
- 数据库文件与表职责描述一致

**Step 3: Final diff check**

Run:
- `git diff --check`
- `Get-ChildItem docs\\architecture`
