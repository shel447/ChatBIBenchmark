# 智能报告评测设计文档

> 日期：2026-03-17  
> 项目：ChatBIBenchmark  
> 目标：补齐“智能报告评测”的可执行设计与落地实现要点

## 1. 目标与范围

本设计聚焦智能报告评测的离线自动化闭环，主判分基于结构化产物与可执行断言，不对 SQL 文本或纯文本相似度做主评分。评测流程覆盖：模板匹配、参数收集、多轮完成度、报告大纲、报告内容一致性。

一期范围：
1. 单数据源执行（SQLite 适配器）。
2. 单租户、内部团队使用。
3. 以结构化产物为核心评测对象，LLM 仅用于辅助解释不计主分。
4. UI 提供最小可用平台（总览、任务列表、任务详情、用例详情）。

## 2. 评测流程

1. **模板匹配**：根据用户目标从候选模板中选择 `template_id`，评测 Top1/TopK。
2. **参数收集**：多轮对话收集 `filled_params`，评测参数精确率/召回率/F1。
3. **多轮完成度**：在 N 轮内 `missing_params` 归零视为完成。
4. **报告大纲**：评测 `outline` 树结构的节点覆盖与层级一致性。
5. **报告内容**：使用 `content_assertions` 的 SQL 执行结果与结构化事实对齐判分。

## 3. 数据集结构

### 3.1 模板库 `report_template`
字段：
1. `template_id`
2. `name`
3. `description`
4. `required_params`
5. `optional_params`
6. `section_schema`（树形结构）
7. `param_constraints`（枚举、日期范围、取值限制）

### 3.2 用例 `report_case`
字段：
1. `case_id`
2. `user_goal`
3. `domain`
4. `available_templates`
5. `expected_template_id`
6. `dialogue_script`
7. `param_ground_truth`
8. `outline_ground_truth`
9. `content_assertions`
10. `difficulty`
11. `tags`

### 3.3 参考答案结构
1. `param_ground_truth`：标准参数 JSON，包含类型与归一化规则。
2. `outline_ground_truth`：章节树结构，包含层级与顺序。
3. `content_assertions`：SQL + 期望值/范围 + 容差 + 维度键。
4. `dialogue_script`：模拟多轮对话，驱动参数收集评测。

## 4. 指标体系

1. 模板命中：`Top1 / TopK Accuracy`
2. 参数填充：`Precision / Recall / F1`
3. 多轮完成度：`Completion Within N Turns`
4. 大纲一致性：`Outline Structure F1`
5. 内容一致性：`Content Assertion Pass Rate`

## 5. 系统架构

核心模块：
1. **Query Adapter**：执行断言 SQL（当前为 SQLite 适配器）。
2. **Evaluator**：计算模板、参数、完成度、大纲、内容评分。
3. **Metadata Store**：SQLite 保存评测 Run 与用例结果。
4. **API 服务**：提供评测与结果写入接口。
5. **前端 UI**：最小可用平台展示评测结果。

## 6. API 与数据模型

### 6.1 API
1. `POST /api/report/evaluate`：对单个用例进行评测。
2. `POST /api/report/runs`：评测并写入元数据。
3. `GET /api/report/templates`：读取模板列表。
4. `GET /api/report/cases`：读取用例列表。

### 6.2 结构化产物
必须输出：
1. `selected_template_id`
2. `filled_params`
3. `missing_params`
4. `outline`
5. `report_json`（包含 `facts`）

## 7. UI 设计

风格：轻盈理性，低饱和、留白、强调层级。

页面：
1. 总览：核心指标、失败分布、近期评测。
2. 评测任务：可筛选列表、得分对比。
3. 任务详情：维度评分、失败用例列表。
4. 用例详情：对话、结构化产物、断言对比。

## 8. 错误处理

1. SQL 执行失败：标记 `error`，计入错误率。
2. 断言无法执行：不计通过，记录原因。
3. 参数类型不匹配：计入参数错误并输出差异详情。
4. 大纲缺失：结构 F1 下降，记录缺失节点。

## 9. 测试策略

1. 评测器：模板、参数、完成度、大纲、内容断言单测覆盖。
2. 存储层：SQLite 写入与读取单测覆盖。
3. 前端路由：根路径重定向与页面可访问性测试。

## 10. 后续扩展

1. 多数据源适配（Postgres、MySQL、ClickHouse）。
2. 指标语义层接入（Cube/MetricFlow）。
3. 报告内容的更细颗粒评测（章节级断言）。
4. 评测任务批量化调度与版本对比。
