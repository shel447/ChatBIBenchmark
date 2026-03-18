import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from backend.core.domain.metric_set import MetricSet
from backend.core.domain.run import Run
from backend.core.domain.run_case_result import RunCaseResult
from backend.core.domain.schedule import ScheduleJob
from backend.core.domain.task import Task


SCHEMA = """
create table if not exists eval_task (
  task_id text primary key,
  name text not null,
  case_set_id text not null,
  environment_id text not null,
  metric_set_id text not null,
  repeat_count integer not null,
  launch_mode text not null,
  task_status text not null,
  created_at text not null,
  updated_at text not null,
  latest_execution_id text
);

create table if not exists eval_run (
  run_id text primary key,
  task_id text,
  name text not null,
  case_set_id text not null,
  environment_id text not null,
  metric_set_id text not null,
  repeat_count integer not null,
  total_cases integer not null,
  executed_cases integer not null,
  accuracy real not null,
  status text not null default 'running',
  trigger_source text not null,
  execution_status text not null,
  started_at text not null,
  ended_at text
);

create table if not exists eval_run_case_result (
  run_id text not null,
  task_id text,
  case_set_id text not null,
  case_id text not null,
  case_title text not null,
  case_type text not null,
  accuracy real not null,
  status text not null,
  issue_tags_json text not null,
  detail_metrics_json text not null,
  summary text not null,
  created_at text not null,
  updated_at text not null,
  primary key (run_id, case_id)
);

create table if not exists schedule_job (
  schedule_id text primary key,
  name text not null,
  task_id text not null,
  schedule_type text not null,
  run_at text,
  daily_time text,
  timezone text not null,
  schedule_status text not null,
  last_triggered_at text,
  next_triggered_at text,
  created_at text not null,
  updated_at text not null
);

create table if not exists metric_set (
  metric_set_id text primary key,
  name text not null,
  scenario_type text not null,
  description text not null,
  score_formula text not null,
  pass_threshold real not null,
  dimensions_json text not null,
  benchmark_refs_json text not null,
  created_at text not null,
  updated_at text not null
);
"""


SEEDED_METRIC_SETS = [
    {
        "metric_set_id": "metric-default",
        "name": "ChatBI 通用发布基线",
        "scenario_type": "通用",
        "description": "适合作为默认上线门槛，强调结果可用、结构正确和事实一致三件事。",
        "score_formula": "weighted_sum_with_gates",
        "pass_threshold": 0.82,
        "dimensions": [
            {
                "key": "result_utility",
                "name": "结果可用性",
                "measurement": "查询/图表/报告能够成功生成并可被业务消费的 case 占比",
                "weight": 0.4,
                "target": 0.9,
                "hard_gate": True,
                "business_value": "先保证系统产物能用，再谈更细粒度质量。",
            },
            {
                "key": "structure_correctness",
                "name": "结构正确性",
                "measurement": "SQL 结果、图表结构或报告大纲与标准答案结构一致度",
                "weight": 0.25,
                "target": 0.82,
                "hard_gate": True,
                "business_value": "防止看起来有内容但结构性错误。",
            },
            {
                "key": "task_success",
                "name": "任务完成率",
                "measurement": "在限定步骤或轮次内完成用户目标的 case 占比",
                "weight": 0.2,
                "target": 0.8,
                "hard_gate": False,
                "business_value": "衡量真实业务流程是否走通。",
            },
            {
                "key": "factual_precision",
                "name": "事实精度",
                "measurement": "原子事实或内容断言通过率",
                "weight": 0.15,
                "target": 0.9,
                "hard_gate": True,
                "business_value": "避免最终产物出现误导性结论。",
            },
        ],
        "benchmark_refs": [
            {"title": "Spider 2.0", "url": "https://spider2-sql.github.io/", "note": "真实企业级 text-to-SQL 难度与执行成功率基线"},
            {"title": "Text2Vis", "url": "https://arxiv.org/abs/2507.19969", "note": "文本生成可视化的代码执行、图表准确性与可读性"},
            {"title": "MultiWOZ Evaluation", "url": "https://github.com/Tomiinek/MultiWOZ_Evaluation", "note": "任务成功率与对话任务完成度"},
            {"title": "FActScore", "url": "https://aclanthology.org/2023.emnlp-main.741/", "note": "长文本事实精度与原子事实验证"},
        ],
    },
    {
        "metric_set_id": "metric-strict",
        "name": "ChatBI 严格发布门禁",
        "scenario_type": "通用",
        "description": "用于发版前回归，抬高事实正确性和可执行性门槛。",
        "score_formula": "weighted_sum_with_gates",
        "pass_threshold": 0.9,
        "dimensions": [
            {
                "key": "result_utility",
                "name": "结果可用性",
                "measurement": "查询/图表/报告能够成功生成并可被业务消费的 case 占比",
                "weight": 0.35,
                "target": 0.95,
                "hard_gate": True,
                "business_value": "严控线上不可用结果。",
            },
            {
                "key": "structure_correctness",
                "name": "结构正确性",
                "measurement": "SQL 结果、图表结构或报告大纲与标准答案结构一致度",
                "weight": 0.2,
                "target": 0.88,
                "hard_gate": True,
                "business_value": "保证结构输出几乎无偏差。",
            },
            {
                "key": "task_success",
                "name": "任务成功率",
                "measurement": "在限定步骤或轮次内完成用户目标的 case 占比",
                "weight": 0.15,
                "target": 0.85,
                "hard_gate": False,
                "business_value": "避免任务链路走到一半失败。",
            },
            {
                "key": "factual_precision",
                "name": "事实精度",
                "measurement": "原子事实或内容断言通过率",
                "weight": 0.3,
                "target": 0.95,
                "hard_gate": True,
                "business_value": "发版前对事实性要求更高。",
            },
        ],
        "benchmark_refs": [
            {"title": "Spider 2.0", "url": "https://spider2-sql.github.io/", "note": "企业级 SQL 真实执行成功率"},
            {"title": "Text2Vis", "url": "https://arxiv.org/abs/2507.19969", "note": "可视化代码执行与图表正确性"},
            {"title": "FActScore", "url": "https://aclanthology.org/2023.emnlp-main.741/", "note": "长文本事实精度"},
        ],
    },
    {
        "metric_set_id": "metric-nl2sql-exec",
        "name": "NL2SQL 执行可靠性",
        "scenario_type": "NL2SQL",
        "description": "参照 Spider/BIRD 的执行导向评测，强调执行结果正确而非 SQL 字符串命中。",
        "score_formula": "weighted_sum_with_gates",
        "pass_threshold": 0.84,
        "dimensions": [
            {
                "key": "execution_accuracy",
                "name": "执行准确率",
                "measurement": "预测 SQL 执行结果与标准结果一致的 case 占比",
                "weight": 0.45,
                "target": 0.85,
                "hard_gate": True,
                "business_value": "最直接反映回答是否正确。",
            },
            {
                "key": "test_suite_accuracy",
                "name": "测试套件准确率",
                "measurement": "通过等价 SQL 测试套件的 case 占比",
                "weight": 0.3,
                "target": 0.8,
                "hard_gate": True,
                "business_value": "避免只记住单个 SQL 形式而忽略语义等价。",
            },
            {
                "key": "executable_rate",
                "name": "可执行率",
                "measurement": "生成 SQL 可以无异常执行的 case 占比",
                "weight": 0.15,
                "target": 0.98,
                "hard_gate": True,
                "business_value": "减少线上报错和空响应。",
            },
            {
                "key": "result_stability",
                "name": "结果稳定率",
                "measurement": "重复执行结果 hash 一致的 case 占比",
                "weight": 0.1,
                "target": 0.95,
                "hard_gate": False,
                "business_value": "防止非确定性输出影响体验。",
            },
        ],
        "benchmark_refs": [
            {"title": "Spider 2.0", "url": "https://spider2-sql.github.io/", "note": "真实企业工作流下的成功率导向 text-to-SQL 基线"},
            {"title": "BIRD-SQL", "url": "https://bird-bench.github.io/", "note": "执行准确率为核心的 text-to-SQL benchmark"},
        ],
    },
    {
        "metric_set_id": "metric-nl2chart-fidelity",
        "name": "NL2CHART 图表保真",
        "scenario_type": "NL2CHART",
        "description": "兼顾图表能否成功渲染、图表类型是否选对，以及数据绑定与视觉结构保真度。",
        "score_formula": "weighted_sum_with_gates",
        "pass_threshold": 0.83,
        "dimensions": [
            {
                "key": "render_success_rate",
                "name": "渲染成功率",
                "measurement": "图表 spec 能成功渲染的 case 占比",
                "weight": 0.3,
                "target": 0.98,
                "hard_gate": True,
                "business_value": "无渲染结果的图表没有业务价值。",
            },
            {
                "key": "chart_type_accuracy",
                "name": "图表类型准确率",
                "measurement": "预测图表类型与标准图表类型一致的 case 占比",
                "weight": 0.25,
                "target": 0.9,
                "hard_gate": True,
                "business_value": "图表类型选错会直接误导分析。",
            },
            {
                "key": "field_binding_f1",
                "name": "字段绑定 F1",
                "measurement": "x/y/series/filter 等字段绑定与标准答案的 F1",
                "weight": 0.25,
                "target": 0.85,
                "hard_gate": False,
                "business_value": "保证图表承载的是对的数据关系。",
            },
            {
                "key": "chart_fidelity_score",
                "name": "图表结构保真分",
                "measurement": "基于 spec 树或渲染结果的结构/视觉保真度评分",
                "weight": 0.2,
                "target": 0.8,
                "hard_gate": False,
                "business_value": "避免图表虽然能渲染，但表达效果走样。",
            },
        ],
        "benchmark_refs": [
            {"title": "Text2Vis", "url": "https://arxiv.org/abs/2507.19969", "note": "answer correctness、code execution success、chart accuracy、readability"},
            {"title": "Chart2Code", "url": "https://arxiv.org/abs/2510.17932", "note": "code-based evaluation 与 chart-quality assessment"},
        ],
    },
    {
        "metric_set_id": "metric-report-dialogue",
        "name": "报告多轮交互生成",
        "scenario_type": "报告多轮交互",
        "description": "覆盖模板选择、参数收集、多轮完成、报告结构和内容事实精度。",
        "score_formula": "weighted_sum_with_gates",
        "pass_threshold": 0.85,
        "dimensions": [
            {
                "key": "template_top1_accuracy",
                "name": "模板 Top1 命中率",
                "measurement": "选中的模板与标准模板一致的 case 占比",
                "weight": 0.2,
                "target": 0.9,
                "hard_gate": True,
                "business_value": "模板选错时后续参数与内容都容易错位。",
            },
            {
                "key": "param_slot_f1",
                "name": "参数槽位 F1",
                "measurement": "参数填充结果与标准参数的精确率/召回率综合",
                "weight": 0.25,
                "target": 0.85,
                "hard_gate": True,
                "business_value": "参数是报告生成的关键信号源。",
            },
            {
                "key": "task_success_rate",
                "name": "任务成功率",
                "measurement": "在限定轮次内完成参数收集并生成报告的 case 占比",
                "weight": 0.2,
                "target": 0.8,
                "hard_gate": True,
                "business_value": "衡量用户目标是否真正完成。",
            },
            {
                "key": "turn_efficiency",
                "name": "轮次效率",
                "measurement": "5 轮内完成的 case 占比",
                "weight": 0.1,
                "target": 0.75,
                "hard_gate": False,
                "business_value": "避免对话拖沓影响体验。",
            },
            {
                "key": "outline_structure_f1",
                "name": "大纲结构 F1",
                "measurement": "章节节点覆盖与层级顺序的结构 F1",
                "weight": 0.1,
                "target": 0.8,
                "hard_gate": False,
                "business_value": "保证报告骨架合理完整。",
            },
            {
                "key": "factual_precision",
                "name": "事实精度",
                "measurement": "内容断言或原子事实通过率",
                "weight": 0.15,
                "target": 0.9,
                "hard_gate": True,
                "business_value": "报告内容必须经得起事实核验。",
            },
        ],
        "benchmark_refs": [
            {"title": "MultiWOZ Evaluation", "url": "https://github.com/Tomiinek/MultiWOZ_Evaluation", "note": "Inform/Success 与 DST slot precision/recall/F1"},
            {"title": "FActScore", "url": "https://aclanthology.org/2023.emnlp-main.741/", "note": "长文本原子事实精度"},
        ],
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_metric_sets(conn: sqlite3.Connection) -> None:
    now = _utc_now()
    for item in SEEDED_METRIC_SETS:
        conn.execute(
            "insert into metric_set(metric_set_id, name, scenario_type, description, score_formula, pass_threshold, dimensions_json, benchmark_refs_json, created_at, updated_at) "
            "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item["metric_set_id"],
                item["name"],
                item["scenario_type"],
                item["description"],
                item["score_formula"],
                item["pass_threshold"],
                json.dumps(item["dimensions"], ensure_ascii=False),
                json.dumps(item["benchmark_refs"], ensure_ascii=False),
                now,
                now,
            ),
        )


def _connect(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    cur = conn.execute(f"pragma table_info({table_name})")
    columns = {row[1] for row in cur.fetchall()}
    if column_name not in columns:
        conn.execute(f"alter table {table_name} add column {column_name} {definition}")


def init_run_db(db_path: str) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA)
        _ensure_column(conn, "eval_run", "status", "text not null default 'running'")
        _ensure_column(conn, "eval_run", "task_id", "text")
        _ensure_column(conn, "eval_run", "trigger_source", "text not null default 'legacy'")
        _ensure_column(conn, "eval_run", "execution_status", "text not null default 'running'")
        cur = conn.execute("select count(1) from metric_set")
        if cur.fetchone()[0] == 0:
            _seed_metric_sets(conn)
        conn.commit()
    finally:
        conn.close()


def _task_from_row(row) -> Task:
    return Task(
        task_id=row[0],
        name=row[1],
        case_set_id=row[2],
        environment_id=row[3],
        metric_set_id=row[4],
        repeat_count=row[5],
        launch_mode=row[6],
        task_status=row[7],
        created_at=row[8],
        updated_at=row[9],
        latest_execution_id=row[10],
    )


def _run_from_row(row) -> Run:
    return Run(
        run_id=row[0],
        task_id=row[1],
        name=row[2],
        case_set_id=row[3],
        environment_id=row[4],
        metric_set_id=row[5],
        repeat_count=row[6],
        total_cases=row[7],
        executed_cases=row[8],
        accuracy=row[9],
        trigger_source=row[10],
        execution_status=row[11],
        started_at=row[12],
        ended_at=row[13],
    )


def _run_case_result_from_row(row) -> RunCaseResult:
    return RunCaseResult(
        run_id=row[0],
        task_id=row[1],
        case_set_id=row[2],
        case_id=row[3],
        case_title=row[4],
        case_type=row[5],
        accuracy=row[6],
        status=row[7],
        issue_tags=json.loads(row[8] or "[]"),
        detail_metrics=json.loads(row[9] or "{}"),
        summary=row[10],
        created_at=row[11],
        updated_at=row[12],
    )


def _schedule_from_row(row) -> ScheduleJob:
    return ScheduleJob(
        schedule_id=row[0],
        name=row[1],
        task_id=row[2],
        schedule_type=row[3],
        run_at=row[4],
        daily_time=row[5],
        timezone=row[6],
        schedule_status=row[7],
        last_triggered_at=row[8],
        next_triggered_at=row[9],
        created_at=row[10],
        updated_at=row[11],
    )


def _metric_set_from_row(row) -> MetricSet:
    return MetricSet(
        metric_set_id=row[0],
        name=row[1],
        scenario_type=row[2],
        description=row[3],
        score_formula=row[4],
        pass_threshold=row[5],
        dimensions=json.loads(row[6] or "[]"),
        benchmark_refs=json.loads(row[7] or "[]"),
        created_at=row[8],
        updated_at=row[9],
    )


class SqliteTaskRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_run_db(db_path)

    def create(self, task: Task) -> Task:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "insert into eval_task(task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, launch_mode, task_status, created_at, updated_at, latest_execution_id) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task.task_id,
                    task.name,
                    task.case_set_id,
                    task.environment_id,
                    task.metric_set_id,
                    task.repeat_count,
                    task.launch_mode,
                    task.task_status,
                    task.created_at,
                    task.updated_at,
                    task.latest_execution_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return task

    def update(self, task: Task) -> Task:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "update eval_task set name = ?, case_set_id = ?, environment_id = ?, metric_set_id = ?, repeat_count = ?, launch_mode = ?, task_status = ?, created_at = ?, updated_at = ?, latest_execution_id = ? where task_id = ?",
                (
                    task.name,
                    task.case_set_id,
                    task.environment_id,
                    task.metric_set_id,
                    task.repeat_count,
                    task.launch_mode,
                    task.task_status,
                    task.created_at,
                    task.updated_at,
                    task.latest_execution_id,
                    task.task_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return task

    def list(self, limit: int = 50) -> List[Task]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, launch_mode, task_status, created_at, updated_at, latest_execution_id "
                "from eval_task order by updated_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_task_from_row(row) for row in rows]

    def get(self, task_id: str) -> Optional[Task]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, launch_mode, task_status, created_at, updated_at, latest_execution_id "
                "from eval_task where task_id = ?",
                (task_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _task_from_row(row) if row else None


class SqliteRunRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_run_db(db_path)

    def create(self, run: Run) -> Run:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "insert into eval_run(run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, status, trigger_source, execution_status, started_at, ended_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.run_id,
                    run.task_id,
                    run.name,
                    run.case_set_id,
                    run.environment_id,
                    run.metric_set_id,
                    run.repeat_count,
                    run.total_cases,
                    run.executed_cases,
                    run.accuracy,
                    run.execution_status,
                    run.trigger_source,
                    run.execution_status,
                    run.started_at,
                    run.ended_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return run

    def update(self, run: Run) -> Run:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "update eval_run set task_id = ?, name = ?, case_set_id = ?, environment_id = ?, metric_set_id = ?, repeat_count = ?, total_cases = ?, executed_cases = ?, accuracy = ?, status = ?, trigger_source = ?, execution_status = ?, started_at = ?, ended_at = ? where run_id = ?",
                (
                    run.task_id,
                    run.name,
                    run.case_set_id,
                    run.environment_id,
                    run.metric_set_id,
                    run.repeat_count,
                    run.total_cases,
                    run.executed_cases,
                    run.accuracy,
                    run.execution_status,
                    run.trigger_source,
                    run.execution_status,
                    run.started_at,
                    run.ended_at,
                    run.run_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return run

    def list(self, limit: int = 50) -> List[Run]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, trigger_source, execution_status, started_at, ended_at "
                "from eval_run order by started_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_run_from_row(row) for row in rows]

    def list_by_task(self, task_id: str, limit: int = 50) -> List[Run]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, trigger_source, execution_status, started_at, ended_at "
                "from eval_run where task_id = ? order by started_at desc limit ?",
                (task_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_run_from_row(row) for row in rows]

    def list_by_case_set(self, case_set_id: str, limit: int = 100) -> List[Run]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, trigger_source, execution_status, started_at, ended_at "
                "from eval_run where case_set_id = ? order by started_at asc limit ?",
                (case_set_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_run_from_row(row) for row in rows]

    def get(self, run_id: str) -> Optional[Run]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, name, case_set_id, environment_id, metric_set_id, repeat_count, total_cases, executed_cases, accuracy, trigger_source, execution_status, started_at, ended_at "
                "from eval_run where run_id = ?",
                (run_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _run_from_row(row) if row else None

    def replace_case_results(self, run_id: str, results: List[RunCaseResult]) -> List[RunCaseResult]:
        conn = _connect(self.db_path)
        try:
            conn.execute("delete from eval_run_case_result where run_id = ?", (run_id,))
            for item in results:
                conn.execute(
                    "insert into eval_run_case_result(run_id, task_id, case_set_id, case_id, case_title, case_type, accuracy, status, issue_tags_json, detail_metrics_json, summary, created_at, updated_at) "
                    "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        item.run_id,
                        item.task_id,
                        item.case_set_id,
                        item.case_id,
                        item.case_title,
                        item.case_type,
                        item.accuracy,
                        item.status,
                        json.dumps(item.issue_tags, ensure_ascii=False),
                        json.dumps(item.detail_metrics, ensure_ascii=False),
                        item.summary,
                        item.created_at,
                        item.updated_at,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        return results

    def list_case_results(self, run_id: str) -> List[RunCaseResult]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select run_id, task_id, case_set_id, case_id, case_title, case_type, accuracy, status, issue_tags_json, detail_metrics_json, summary, created_at, updated_at "
                "from eval_run_case_result where run_id = ? order by case_id asc",
                (run_id,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_run_case_result_from_row(row) for row in rows]

    def list_case_history(self, case_set_id: str, case_id: str, limit: int = 100) -> List[RunCaseResult]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select r.run_id, c.task_id, c.case_set_id, c.case_id, c.case_title, c.case_type, c.accuracy, c.status, c.issue_tags_json, c.detail_metrics_json, c.summary, c.created_at, c.updated_at "
                "from eval_run_case_result c join eval_run r on r.run_id = c.run_id "
                "where c.case_set_id = ? and c.case_id = ? order by r.started_at asc limit ?",
                (case_set_id, case_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_run_case_result_from_row(row) for row in rows]


class SqliteScheduleRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_run_db(db_path)

    def create(self, schedule: ScheduleJob) -> ScheduleJob:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "insert into schedule_job(schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    schedule.schedule_id,
                    schedule.name,
                    schedule.task_id,
                    schedule.schedule_type,
                    schedule.run_at,
                    schedule.daily_time,
                    schedule.timezone,
                    schedule.schedule_status,
                    schedule.last_triggered_at,
                    schedule.next_triggered_at,
                    schedule.created_at,
                    schedule.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return schedule

    def update(self, schedule: ScheduleJob) -> ScheduleJob:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "update schedule_job set name = ?, task_id = ?, schedule_type = ?, run_at = ?, daily_time = ?, timezone = ?, schedule_status = ?, last_triggered_at = ?, next_triggered_at = ?, created_at = ?, updated_at = ? where schedule_id = ?",
                (
                    schedule.name,
                    schedule.task_id,
                    schedule.schedule_type,
                    schedule.run_at,
                    schedule.daily_time,
                    schedule.timezone,
                    schedule.schedule_status,
                    schedule.last_triggered_at,
                    schedule.next_triggered_at,
                    schedule.created_at,
                    schedule.updated_at,
                    schedule.schedule_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return schedule

    def delete(self, schedule_id: str) -> None:
        conn = _connect(self.db_path)
        try:
            conn.execute("delete from schedule_job where schedule_id = ?", (schedule_id,))
            conn.commit()
        finally:
            conn.close()

    def list(self, limit: int = 100) -> List[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job order by created_at desc limit ?",
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_schedule_from_row(row) for row in rows]

    def list_due(self, now_iso: str) -> List[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job where schedule_status = 'enabled' and next_triggered_at is not null and next_triggered_at <= ? order by next_triggered_at asc",
                (now_iso,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_schedule_from_row(row) for row in rows]

    def get(self, schedule_id: str) -> Optional[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job where schedule_id = ?",
                (schedule_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _schedule_from_row(row) if row else None

    def get_active_for_task(self, task_id: str) -> Optional[ScheduleJob]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select schedule_id, name, task_id, schedule_type, run_at, daily_time, timezone, schedule_status, last_triggered_at, next_triggered_at, created_at, updated_at "
                "from schedule_job where task_id = ? and schedule_status = 'enabled' order by created_at desc limit 1",
                (task_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _schedule_from_row(row) if row else None


class SqliteMetricSetRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_run_db(db_path)

    def list(self) -> List[MetricSet]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select metric_set_id, name, scenario_type, description, score_formula, pass_threshold, dimensions_json, benchmark_refs_json, created_at, updated_at "
                "from metric_set order by scenario_type asc, created_at asc"
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        return [_metric_set_from_row(row) for row in rows]

    def get(self, metric_set_id: str) -> Optional[MetricSet]:
        conn = _connect(self.db_path)
        try:
            cur = conn.execute(
                "select metric_set_id, name, scenario_type, description, score_formula, pass_threshold, dimensions_json, benchmark_refs_json, created_at, updated_at "
                "from metric_set where metric_set_id = ?",
                (metric_set_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()
        return _metric_set_from_row(row) if row else None

    def create(self, metric_set: MetricSet) -> MetricSet:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "insert into metric_set(metric_set_id, name, scenario_type, description, score_formula, pass_threshold, dimensions_json, benchmark_refs_json, created_at, updated_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    metric_set.metric_set_id,
                    metric_set.name,
                    metric_set.scenario_type,
                    metric_set.description,
                    metric_set.score_formula,
                    metric_set.pass_threshold,
                    json.dumps(metric_set.dimensions, ensure_ascii=False),
                    json.dumps(metric_set.benchmark_refs, ensure_ascii=False),
                    metric_set.created_at,
                    metric_set.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return metric_set

    def update(self, metric_set: MetricSet) -> MetricSet:
        conn = _connect(self.db_path)
        try:
            conn.execute(
                "update metric_set set name = ?, scenario_type = ?, description = ?, score_formula = ?, pass_threshold = ?, dimensions_json = ?, benchmark_refs_json = ?, created_at = ?, updated_at = ? where metric_set_id = ?",
                (
                    metric_set.name,
                    metric_set.scenario_type,
                    metric_set.description,
                    metric_set.score_formula,
                    metric_set.pass_threshold,
                    json.dumps(metric_set.dimensions, ensure_ascii=False),
                    json.dumps(metric_set.benchmark_refs, ensure_ascii=False),
                    metric_set.created_at,
                    metric_set.updated_at,
                    metric_set.metric_set_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return metric_set
