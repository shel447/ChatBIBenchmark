# 用例集 Excel 导入导出设计

## 背景
当前用例集页面仅为静态展示，不支持真实的 Excel 导入、导出与覆盖更新。用户需要：
- 修正侧边栏在切换到其它页面时“总览”按钮仍保留单独底框的问题。
- 在用例集列表页面支持批量导出多个用例集。
- 在单个用例集页面支持“更新用例集”和“导出当前用例集”。
- 导入与导出都需要真实走后端，并以 SQLite 为后端存储。

## 目标
- 用例集列表页支持“导出模式”，进入后可勾选多个用例集并分别下载多个 `.xlsx` 文件。
- 单个用例集页支持上传一个 Excel 文件覆盖当前用例集。
- 后端提供真实的 Excel 解析与生成能力。
- Excel 模板按用例类型区分，不采用统一列模板。

## 非目标
- 不实现 ZIP 打包下载。
- 不实现复杂权限、审计或历史版本管理。
- 不把整个用例集页面改造成前端框架应用，仍保持原生 HTML/CSS/JS。

## Excel 模板
### NL2SQL
- `case_id`
- `question`
- `expected_sql`

### NL2CHART
- `case_id`
- `question`
- `sql`
- `expected_chart_type`

### 智能问数（E2E）
- `case_id`
- `question`
- `expected_sql`
- `expected_chart_type`

### 报告多轮交互
- `case_id`
- `user_goal`
- `template_name`
- `dialogue_script`
- `param_ground_truth`
- `outline_ground_truth`
- `content_assertions`

说明：
- 报告多轮交互中的 `dialogue_script`、`param_ground_truth`、`outline_ground_truth`、`content_assertions` 以 JSON 字符串形式存储在单元格中。
- `template_name` 用于评测模板匹配结果，当前阶段不再额外引入 `template_id`。

## 数据模型
### case_set
- `id`
- `name`
- `type`
- `description`
- `tags_json`
- `is_seed`
- `schema_version`
- `created_at`
- `updated_at`

### case_item
- `id`
- `case_set_id`
- `case_id`
- `title`
- `payload_json`
- `created_at`
- `updated_at`

说明：
- `payload_json` 按用例类型存放对应字段。
- 导入覆盖时删除该用例集原有 `case_item`，再写入新记录。

## 后端接口
### `GET /api/case-sets`
返回用例集列表，包含类型、名称、描述、是否种子等元数据。

### `GET /api/case-sets/{case_set_id}`
返回单个用例集及其用例明细。

### `GET /api/case-sets/{case_set_id}/export`
根据用例集类型生成一个 `.xlsx` 文件并返回下载响应。

### `POST /api/case-sets/{case_set_id}/import`
接收上传的 `.xlsx` 文件，按当前用例集类型解析并覆盖该用例集的用例。

## 前端交互
### 侧边栏
- 去除 `总览` 的独占样式，所有菜单保持一致。

### 用例集列表页
- 页头按钮：`导入用例`、`导出用例集`
- 点击 `导出用例集` 后进入导出模式：
  - 卡片显示复选框
  - 页头切换为 `导出所选`、`取消`
  - 显示已选数量
- 点击 `导出所选` 后，对每个选中的用例集分别发起一次下载。

### 单个用例集页
- 页头按钮：`更新用例集`、`导出当前用例集`
- `更新用例集` 触发文件选择器，上传成功后覆盖当前用例集。
- `导出当前用例集` 直接下载当前用例集的 Excel。

## 校验规则
- Excel 首行列名必须与对应类型模板完全匹配。
- `case_id` 必填，且同一文件内唯一。
- 报告类 JSON 字段必须能被解析。
- 解析失败返回 400 与明确错误信息。

## 技术实现
- 使用 `openpyxl` 生成和解析 `.xlsx`。
- 生成的工作簿只包含一个 sheet，sheet 名使用用例集名称截断后的安全名称。
- 批量导出由前端循环调用单个导出接口，不在服务端打包。

## 测试计划
- 后端：
  - 导出单个用例集返回正确的 `.xlsx`
  - 导入合法 `.xlsx` 后覆盖原有用例
  - 非法模板导入返回 400
- 前端：
  - 路由页面包含 `导出用例集`、`导出所选`、`更新用例集` 文案
  - 侧边栏样式类调整后，`总览` 不再有独占底框样式
