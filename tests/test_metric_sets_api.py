import os
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import backend.app as app_module

DB_DIR = os.path.join(ROOT, "backend")


class MetricSetApiTests(unittest.TestCase):
    def setUp(self):
        self.db_paths = []
        self.meta_db = self._make_db_path("report-eval-")
        self.run_db = self._make_db_path("runs-")
        self.case_set_db = self._make_db_path("case-sets-")
        app_module.DEFAULT_META_DB = self.meta_db
        app_module.DEFAULT_RUN_DB = self.run_db
        app_module.DEFAULT_CASE_SET_DB = self.case_set_db

    def tearDown(self):
        for path in self.db_paths:
            if os.path.exists(path):
                os.remove(path)

    def _make_db_path(self, prefix):
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=".db", dir=DB_DIR)
        os.close(fd)
        self.db_paths.append(path)
        return path

    def test_list_metric_sets_returns_industry_presets(self):
        with TestClient(app_module.app) as client:
            response = client.get("/api/metric-sets")
            self.assertEqual(response.status_code, 200)
            payload = response.json()["metric_sets"]
            metric_ids = {item["metric_set_id"] for item in payload}
            self.assertIn("metric-nl2sql-exec", metric_ids)
            self.assertIn("metric-nl2chart-fidelity", metric_ids)
            self.assertIn("metric-report-dialogue", metric_ids)

    def test_get_metric_set_detail_contains_dimensions_and_sources(self):
        with TestClient(app_module.app) as client:
            response = client.get("/api/metric-sets/metric-report-dialogue")
            self.assertEqual(response.status_code, 200)
            metric_set = response.json()["metric_set"]
            dimension_names = {item["name"] for item in metric_set["dimensions"]}
            ref_titles = {item["title"] for item in metric_set["benchmark_refs"]}
            self.assertIn("模板 Top1 命中率", dimension_names)
            self.assertIn("任务成功率", dimension_names)
            self.assertIn("事实精度", dimension_names)
            self.assertTrue(any("FActScore" in title for title in ref_titles))

    def test_create_metric_set_supports_custom_weights(self):
        payload = {
            "name": "NL2SQL 发布门禁 - 自定义",
            "scenario_type": "NL2SQL",
            "description": "更强调执行正确性与稳定性。",
            "score_formula": "weighted_sum_with_gates",
            "pass_threshold": 0.88,
            "dimensions": [
                {
                    "key": "execution_accuracy",
                    "name": "执行准确率",
                    "measurement": "执行结果与标准结果一致的 case 占比",
                    "weight": 0.6,
                    "target": 0.9,
                    "hard_gate": True,
                    "business_value": "直接衡量查询答案是否可用",
                },
                {
                    "key": "test_suite_accuracy",
                    "name": "测试套件准确率",
                    "measurement": "通过等价查询测试集的 case 占比",
                    "weight": 0.4,
                    "target": 0.82,
                    "hard_gate": False,
                    "business_value": "降低仅靠单一 SQL 命中的偶然性",
                },
            ],
            "benchmark_refs": [
                {
                    "title": "Spider Test Suite Accuracy",
                    "url": "https://yale-lily.github.io/spider",
                    "note": "文本到 SQL 常用鲁棒性指标",
                }
            ],
        }
        with TestClient(app_module.app) as client:
            create_resp = client.post("/api/metric-sets", json=payload)
            self.assertEqual(create_resp.status_code, 200)
            metric_set = create_resp.json()["metric_set"]
            self.assertEqual(metric_set["name"], payload["name"])
            self.assertEqual(metric_set["dimensions"][0]["weight"], 0.6)

            list_resp = client.get("/api/metric-sets")
            self.assertEqual(list_resp.status_code, 200)
            self.assertTrue(any(item["metric_set_id"] == metric_set["metric_set_id"] for item in list_resp.json()["metric_sets"]))

    def test_patch_metric_set_updates_thresholds(self):
        with TestClient(app_module.app) as client:
            detail_resp = client.get("/api/metric-sets/metric-nl2chart-fidelity")
            self.assertEqual(detail_resp.status_code, 200)
            metric_set = detail_resp.json()["metric_set"]
            dimensions = metric_set["dimensions"]
            dimensions[0]["target"] = 0.99
            dimensions[0]["weight"] = 0.35

            patch_resp = client.patch(
                "/api/metric-sets/metric-nl2chart-fidelity",
                json={
                    "pass_threshold": 0.86,
                    "dimensions": dimensions,
                },
            )
            self.assertEqual(patch_resp.status_code, 200)
            updated = patch_resp.json()["metric_set"]
            self.assertEqual(updated["pass_threshold"], 0.86)
            self.assertEqual(updated["dimensions"][0]["target"], 0.99)
            self.assertEqual(updated["dimensions"][0]["weight"], 0.35)

    def test_create_task_rejects_unknown_metric_set(self):
        payload = {
            "name": "零售待执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-not-found",
            "repeat_count": 1,
            "launch_mode": "deferred",
        }
        with TestClient(app_module.app) as client:
            response = client.post("/api/tasks", json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertIn("metric_set", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
