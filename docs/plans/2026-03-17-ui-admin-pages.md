# UI 调整与管理界面扩展 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把评测入口下沉到对应页面，完善评测任务列表要素展示，并新增环境配置与指标管理页面。

**Architecture:** 仍为静态单页 HTML/CSS/JS。通过 `data-view` 切换视图，新增的页面与控件仅做静态展示，不接入后端数据与排序逻辑。

**Tech Stack:** HTML + CSS + Vanilla JS（`frontend/` 静态页面），FastAPI 静态文件服务，Python `unittest` 测试。

---

### Task 1: 新增导航与管理页面（环境配置/指标管理）

**Files:**
- Modify: `tests/test_frontend_routes.py`
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`

**Step 1: Write the failing test**

```python
def test_frontend_index_served(self):
    client = TestClient(app)
    response = client.get("/frontend/")
    self.assertEqual(response.status_code, 200)
    self.assertIn("环境配置", response.text)
    self.assertIn("指标管理", response.text)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: FAIL with missing text assertions.

**Step 3: Write minimal implementation**

Add two nav items and two new `<section class="view">` blocks:
- `data-view="env-config"` titled “环境配置”，表格列：环境名、基础地址、状态、最近更新。
- `data-view="metric-sets"` titled “评测指标管理”，表格列：参数集名称、描述、覆盖指标/阈值、最近更新。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_frontend_routes.py frontend/index.html frontend/styles.css
git commit -m "ui: add env and metric management pages"
```

---

### Task 2: 移动页面级按钮（导入用例 / 新增评测）

**Files:**
- Modify: `tests/test_frontend_routes.py`
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`

**Step 1: Write the failing test**

```python
def test_frontend_index_served(self):
    client = TestClient(app)
    response = client.get("/frontend/")
    self.assertIn("导入用例", response.text)
    self.assertIn("新增评测", response.text)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: FAIL because buttons are not placed yet.

**Step 3: Write minimal implementation**

- 移除顶部 `topbar-actions` 按钮区。
- 在“任务列表”页头右侧新增 `新增评测` 按钮。
- 在“用例集”页头右侧新增 `导入用例` 按钮。
- 若需要，新增 `.panel-actions` 与按钮布局样式。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_frontend_routes.py frontend/index.html frontend/styles.css
git commit -m "ui: move action buttons into pages"
```

---

### Task 3: 强化评测任务列表要素与排序/过滤控件

**Files:**
- Modify: `tests/test_frontend_routes.py`
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`

**Step 1: Write the failing test**

```python
def test_frontend_index_served(self):
    client = TestClient(app)
    response = client.get("/frontend/")
    self.assertIn("启动时间", response.text)
    self.assertIn("结束时间", response.text)
    self.assertIn("指标参数集", response.text)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: FAIL with missing column text.

**Step 3: Write minimal implementation**

- 在“任务列表”表头增加列：用例集、环境、启动时间、结束时间、指标参数集。
- 在“启动时间/结束时间”列头各增加上下排序按钮，默认启动时间倒排按钮高亮。
- 增加“用例集”过滤下拉（静态），放置在列表顶部控制区。
- 填充示例行数据，包含环境、用例集、时间与指标参数集。
- 新增 `.sort-group`、`.sort-btn`、`.filter-control` 等样式，保持与现有视觉风格一致。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_frontend_routes.py frontend/index.html frontend/styles.css
git commit -m "ui: expand run list fields and controls"
```

