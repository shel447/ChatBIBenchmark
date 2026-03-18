import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from backend.app import app


class RunApiTests(unittest.TestCase):
    def test_create_list_get_run(self):
        payload = {
            "name": "零售 v1.4",
            "case_set_id": "cs-001",
            "environment_id": "env-001",
            "metric_set_id": "metric-default",
            "repeat_count": 2,
        }
        with TestClient(app) as client:
            create_resp = client.post("/api/runs", json=payload)
            self.assertEqual(create_resp.status_code, 200)
            data = create_resp.json()
            self.assertIn("run", data)
            run = data["run"]
            self.assertEqual(run["case_set_id"], "cs-001")
            self.assertEqual(run["repeat_count"], 2)
            self.assertEqual(run["total_cases"], 0)
            self.assertEqual(run["executed_cases"], 0)
            self.assertEqual(run["accuracy"], 0)

            list_resp = client.get("/api/runs")
            self.assertEqual(list_resp.status_code, 200)
            runs = list_resp.json().get("runs", [])
            self.assertTrue(any(item["run_id"] == run["run_id"] for item in runs))

            detail_resp = client.get(f"/api/runs/{run['run_id']}")
            self.assertEqual(detail_resp.status_code, 200)
            detail = detail_resp.json()["run"]
            self.assertEqual(detail["environment_id"], "env-001")


if __name__ == "__main__":
    unittest.main()
