import os
import sqlite3
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import backend.app as app_module

DB_DIR = os.path.join(ROOT, "backend")


def _build_case(case_id: str, template_name: str = "销售摘要模板", include_assertions: bool = True):
    case_payload = {
        "case_id": case_id,
        "user_goal": "生成一月经营报告",
        "template_name": template_name,
        "param_ground_truth": {
            "date_range": {
                "type": "date_range",
                "value": {"start": "2025-01-01", "end": "2025-01-31"},
            },
            "metric": {"type": "enum", "value": "gmv"},
        },
        "outline_ground_truth": {
            "title": "销售摘要",
            "sections": [
                {"title": "概览", "sections": []},
                {"title": "趋势", "sections": []},
            ],
        },
        "content_assertions": [],
    }
    if include_assertions:
        case_payload["content_assertions"] = [
            {
                "statement_id": "s1",
                "sql": "select sum(amount) from sales",
                "expected_value": 250,
                "tolerance": 0,
            }
        ]
    return case_payload


def _build_output(template_name: str = "销售摘要模板", report_generated: bool = True):
    output_payload = {
        "selected_template_name": template_name,
        "candidate_template_ids": [template_name, "区域分解模板"],
        "filled_params": {
            "date_range": {
                "type": "date_range",
                "value": {"start": "2025-01-01", "end": "2025-01-31"},
            },
            "metric": {"type": "enum", "value": "gmv"},
        },
        "missing_params_by_turn": [["date_range"], []],
        "outline": {
            "title": "销售摘要",
            "sections": [
                {"title": "概览", "sections": []},
                {"title": "趋势", "sections": []},
            ],
        },
        "report_facts": {"s1": 250},
    }
    if report_generated:
        output_payload["report_markdown"] = "# 销售摘要\n"
    return output_payload


class ReportMetricActivationApiTests(unittest.TestCase):
    def setUp(self):
        self.db_paths = []
        self.meta_db = self._make_db_path("report-meta-")
        self.run_db = self._make_db_path("report-runs-")
        self.case_set_db = self._make_db_path("report-case-sets-")
        self.data_db = self._make_db_path("report-data-")
        app_module.DEFAULT_META_DB = self.meta_db
        app_module.DEFAULT_RUN_DB = self.run_db
        app_module.DEFAULT_CASE_SET_DB = self.case_set_db
        self._init_data_db(self.data_db)

    def tearDown(self):
        for path in self.db_paths:
            if os.path.exists(path):
                os.remove(path)

    def _make_db_path(self, prefix):
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=".db", dir=DB_DIR)
        os.close(fd)
        self.db_paths.append(path)
        return path

    def _init_data_db(self, db_path):
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("create table sales(region text, amount integer)")
            conn.executemany(
                "insert into sales(region, amount) values (?, ?)",
                [("east", 100), ("west", 150)],
            )
            conn.commit()
        finally:
            conn.close()

    def test_report_evaluate_returns_aggregated_metrics_when_metric_set_is_supplied(self):
        payload = {
            "case": _build_case("case-1"),
            "output": _build_output(),
            "data_db_path": self.data_db,
            "metric_set_id": "metric-report-dialogue",
        }
        with TestClient(app_module.app) as client:
            response = client.post("/api/report/evaluate", json=payload)
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertIn("raw_metrics", body)
            self.assertIn("applied_metric_set", body)
            self.assertIn("aggregated_metrics", body)
            self.assertEqual(body["applied_metric_set"]["metric_set_id"], "metric-report-dialogue")
            self.assertTrue(body["aggregated_metrics"]["passed"])
            self.assertEqual(len(body["aggregated_metrics"]["dimensions"]), 6)

    def test_report_evaluate_hard_gate_failure_blocks_pass(self):
        payload = {
            "case": _build_case("case-2"),
            "output": _build_output(template_name="区域分解模板"),
            "data_db_path": self.data_db,
            "metric_set_id": "metric-report-dialogue",
        }
        with TestClient(app_module.app) as client:
            response = client.post("/api/report/evaluate", json=payload)
            self.assertEqual(response.status_code, 200)
            aggregated = response.json()["aggregated_metrics"]
            template_dimension = next(item for item in aggregated["dimensions"] if item["key"] == "template_top1_accuracy")
            self.assertFalse(template_dimension["target_passed"])
            self.assertFalse(aggregated["hard_gate_passed"])
            self.assertFalse(aggregated["passed"])

    def test_report_evaluate_rejects_non_report_metric_set(self):
        payload = {
            "case": _build_case("case-3"),
            "output": _build_output(),
            "data_db_path": self.data_db,
            "metric_set_id": "metric-nl2sql-exec",
        }
        with TestClient(app_module.app) as client:
            response = client.post("/api/report/evaluate", json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertIn("报告多轮交互", response.json()["detail"])

    def test_report_evaluate_rejects_missing_required_ground_truth_for_active_dimensions(self):
        case_payload = _build_case("case-4", include_assertions=False)
        case_payload["content_assertions"] = []
        payload = {
            "case": case_payload,
            "output": _build_output(),
            "data_db_path": self.data_db,
            "metric_set_id": "metric-report-dialogue",
        }
        with TestClient(app_module.app) as client:
            response = client.post("/api/report/evaluate", json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertIn("content_assertions", response.json()["detail"])

    def test_report_runs_aggregate_multiple_cases_and_expose_run_queries(self):
        payload_one = {
            "run_id": "run-report-1",
            "case": _build_case("case-a"),
            "output": _build_output(),
            "data_db_path": self.data_db,
            "metric_set_id": "metric-report-dialogue",
        }
        payload_two = {
            "run_id": "run-report-1",
            "case": _build_case("case-b"),
            "output": _build_output(template_name="区域分解模板"),
            "data_db_path": self.data_db,
            "metric_set_id": "metric-report-dialogue",
        }
        with TestClient(app_module.app) as client:
            first = client.post("/api/report/runs", json=payload_one)
            second = client.post("/api/report/runs", json=payload_two)
            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)

            list_response = client.get("/api/report/runs")
            self.assertEqual(list_response.status_code, 200)
            self.assertEqual(list_response.json()["runs"][0]["run_id"], "run-report-1")
            self.assertEqual(list_response.json()["runs"][0]["metrics"]["case_count"], 2)

            detail_response = client.get("/api/report/runs/run-report-1")
            self.assertEqual(detail_response.status_code, 200)
            detail = detail_response.json()
            self.assertEqual(detail["run"]["run_id"], "run-report-1")
            self.assertEqual(detail["run"]["metrics"]["case_count"], 2)
            self.assertEqual(len(detail["case_results"]), 2)
            self.assertLess(detail["run"]["metrics"]["aggregated_summary"]["overall_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
