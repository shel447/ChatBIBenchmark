# 评测任务弹窗与进度条 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 新增评测任务弹窗并与 `/api/runs` 交互，同时在任务列表与详情显示进度条。

**Architecture:** 前端使用原生 HTML/CSS/JS 实现弹窗与进度条；通过 `fetch` 调用后端 API 创建任务；列表插入新行并保持原有视图切换逻辑。

**Tech Stack:** FastAPI (existing API), Vanilla HTML/CSS/JS, unittest

---

### Task 1: 前端路由测试先红

**Files:**
- Modify: `tests/test_frontend_routes.py`

**Step 1: Write the failing assertions**

```python
self.assertIn("创建评测任务", response.text)
self.assertIn("创建并启动", response.text)
self.assertIn("任务名称", response.text)
self.assertIn("进度条", response.text)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: FAIL with missing strings.

**Step 3: Commit**

```bash
git add tests/test_frontend_routes.py
git commit -m "test: assert run modal strings"
```

---

### Task 2: 任务列表与详情添加进度条结构

**Files:**
- Modify: `frontend/index.html`

**Step 1: Update HTML**

- 任务列表“进展”列改为文本 + 进度条结构：
```html
<div class="progress-cell">
  <span class="progress-text">60 / 200</span>
  <div class="progress-bar" aria-label="进度条">
    <div class="progress-fill" style="width: 30%"></div>
  </div>
</div>
```
- 任务详情“进展”卡片内增加相同进度条结构。

**Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "ui: add progress bar structure"
```

---

### Task 3: 新增评测弹窗结构

**Files:**
- Modify: `frontend/index.html`

**Step 1: Add modal markup**

- 在 `body` 末尾新增弹窗结构（包含遮罩、标题、关闭按钮、表单字段、错误提示、按钮区）。
- 表单字段：
  - 任务名称（input）
  - 用例集（select）
  - 环境（select）
  - 指标参数集（select）
  - 用例集执行次数（number input）
- “新增评测”按钮添加 `data-open-run-modal`。
- 关闭按钮与遮罩添加 `data-close-run-modal`。

**Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "ui: add run create modal markup"
```

---

### Task 4: 弹窗与进度条样式

**Files:**
- Modify: `frontend/styles.css`

**Step 1: Add CSS**

- Modal 样式：`.modal`, `.modal.hidden`, `.modal-card`, `.modal-header`, `.modal-body`, `.modal-footer`, `.modal-close`, `.modal-error`。
- Progress 样式：`.progress-cell`, `.progress-text`, `.progress-bar`, `.progress-fill`。
- 表单布局样式：`.form-grid`, `.form-field`。

**Step 2: Commit**

```bash
git add frontend/styles.css
git commit -m "ui: style run modal and progress bars"
```

---

### Task 5: 弹窗交互与 API 调用

**Files:**
- Modify: `frontend/app.js`

**Step 1: Add JS logic**

- 点击“新增评测”打开弹窗。
- 点击遮罩/关闭/取消关闭弹窗。
- 表单校验必填项，错误时显示 `.modal-error`。
- `fetch("/api/runs")` 创建任务，成功后插入表格首行并关闭弹窗。
- 插入行时计算进度条宽度（总数为 0 → 0%）。
- 改为事件委托处理 `[data-view-link]`，确保新增行可点击。

**Step 2: Commit**

```bash
git add frontend/app.js
git commit -m "feat: wire run modal to api and insert row"
```

---

### Task 6: 运行前端测试转绿

**Files:**
- None

**Step 1: Run tests**

Run: `python -m unittest tests/test_frontend_routes.py -v`  
Expected: PASS.

**Step 2: Commit**

```bash
git status -sb
```

