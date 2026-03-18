# 用例集 Excel 导入导出 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为用例集提供真实的 Excel 批量导出、单集导出与覆盖导入，并修正相关前端交互与侧边栏样式。

**Architecture:** 后端新增用例集/用例仓储与 Excel 编解码模块，SQLite 存储用例集及其用例；前端在现有静态页面基础上接入真实 API，增加导出模式、上传覆盖与下载行为。

**Tech Stack:** FastAPI, SQLite, openpyxl, Vanilla HTML/CSS/JS, unittest

---

### Task 1: 写后端 Excel 导入导出测试

**Files:**
- Create: `tests/test_case_sets_api.py`

**Step 1: Write the failing tests**

```python
def test_export_case_set_returns_excel(self):
    ...

def test_import_case_set_overwrites_existing_cases(self):
    ...

def test_import_rejects_invalid_template(self):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_case_sets_api.py -v`
Expected: FAIL with missing route/import support.

**Step 3: Commit**

```bash
git add tests/test_case_sets_api.py
git commit -m "test: add case set excel api tests"
```

---

### Task 2: 新增用例集仓储与 Excel 模块

**Files:**
- Create: `backend/storage/case_set_repository.py`
- Create: `backend/core/domain/case_set.py`
- Create: `backend/core/usecases/case_set_usecases.py`
- Create: `backend/adapters/excel_case_set_adapter.py`

**Step 1: Write minimal implementation**

- 定义 `CaseSet` / `CaseItem` 领域对象
- 建表并初始化种子用例集与示例用例
- 实现不同类型的列模板、工作簿生成与解析

**Step 2: Commit**

```bash
git add backend/storage/case_set_repository.py backend/core/domain/case_set.py backend/core/usecases/case_set_usecases.py backend/adapters/excel_case_set_adapter.py
git commit -m "feat: add case set storage and excel adapter"
```

---

### Task 3: 接入后端 API

**Files:**
- Modify: `backend/app.py`

**Step 1: Implement minimal API**

- `GET /api/case-sets`
- `GET /api/case-sets/{case_set_id}`
- `GET /api/case-sets/{case_set_id}/export`
- `POST /api/case-sets/{case_set_id}/import`

**Step 2: Run tests to verify they pass**

Run: `python -m unittest tests/test_case_sets_api.py -v`
Expected: PASS.

**Step 3: Commit**

```bash
git add backend/app.py
git commit -m "feat: add case set excel apis"
```

---

### Task 4: 写前端页面文案测试

**Files:**
- Modify: `tests/test_frontend_routes.py`

**Step 1: Write the failing assertions**

```python
self.assertIn("导出用例集", response.text)
self.assertIn("导出所选", response.text)
self.assertIn("更新用例集", response.text)
self.assertNotIn("primary-nav", response.text)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_frontend_routes.py -v`
Expected: FAIL with missing strings / unchanged markup.

**Step 3: Commit**

```bash
git add tests/test_frontend_routes.py
git commit -m "test: add case set export ui assertions"
```

---

### Task 5: 调整页面结构与样式

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`

**Step 1: Update HTML**

- 统一侧边栏按钮样式，去掉 `primary-nav`
- 用例集列表页加入导出模式工具条
- 单个用例集页加入 `更新用例集` / `导出当前用例集`
- 增加隐藏文件上传 input

**Step 2: Update CSS**

- 增加导出模式、卡片复选框、按钮状态、成功/错误提示样式

**Step 3: Commit**

```bash
git add frontend/index.html frontend/styles.css
git commit -m "ui: add case set export and import controls"
```

---

### Task 6: 接前端交互与下载上传逻辑

**Files:**
- Modify: `frontend/app.js`

**Step 1: Implement JS**

- 拉取用例集列表并缓存元数据
- 导出模式切换、卡片选择、批量触发下载
- 单集导出按钮下载当前用例集
- 更新用例集按钮触发文件选择并上传覆盖
- 用例集卡片点击后刷新单集详情标题和当前上下文

**Step 2: Run frontend tests**

Run: `python -m unittest tests/test_frontend_routes.py -v`
Expected: PASS.

**Step 3: Commit**

```bash
git add frontend/app.js
git commit -m "feat: wire case set excel actions"
```

---

### Task 7: 回归验证

**Files:**
- None

**Step 1: Run regression tests**

Run:
- `python -m unittest tests/test_case_sets_api.py -v`
- `python -m unittest tests/test_runs_api.py -v`
- `python -m unittest tests/test_frontend_routes.py -v`

Expected: PASS.

**Step 2: Check status**

Run: `git status -sb`

