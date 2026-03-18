import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import backend.app as app_module

DB_DIR = os.path.join(ROOT, "backend")


class TaskScheduleApiTests(unittest.TestCase):
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

    def test_create_deferred_task_does_not_create_execution(self):
        payload = {
            "name": "零售待执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-default",
            "repeat_count": 1,
            "launch_mode": "deferred",
        }
        with TestClient(app_module.app) as client:
            create_resp = client.post("/api/tasks", json=payload)
            self.assertEqual(create_resp.status_code, 200)
            task = create_resp.json()["task"]
            self.assertEqual(task["launch_mode"], "deferred")
            self.assertEqual(task["task_status"], "pending")
            self.assertIsNone(task["latest_execution_id"])

            list_resp = client.get("/api/tasks")
            self.assertEqual(list_resp.status_code, 200)
            tasks = list_resp.json()["tasks"]
            self.assertTrue(any(item["task_id"] == task["task_id"] for item in tasks))

            runs_resp = client.get("/api/runs")
            self.assertEqual(runs_resp.status_code, 200)
            self.assertEqual(runs_resp.json()["runs"], [])

    def test_task_and_schedule_routes_initialize_db_without_lifespan_context(self):
        payload = {
            "name": "零售待执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-default",
            "repeat_count": 1,
            "launch_mode": "deferred",
        }
        client = TestClient(app_module.app)
        tasks_resp = client.get("/api/tasks")
        self.assertEqual(tasks_resp.status_code, 200)
        self.assertEqual(tasks_resp.json()["tasks"], [])

        schedules_resp = client.get("/api/schedules")
        self.assertEqual(schedules_resp.status_code, 200)
        self.assertEqual(schedules_resp.json()["schedules"], [])

        create_resp = client.post("/api/tasks", json=payload)
        self.assertEqual(create_resp.status_code, 200)
        self.assertEqual(create_resp.json()["task"]["launch_mode"], "deferred")

    def test_post_runs_acts_as_immediate_task_compat_alias(self):
        payload = {
            "name": "零售立即执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-default",
            "repeat_count": 1,
        }
        with TestClient(app_module.app) as client:
            create_resp = client.post("/api/runs", json=payload)
            self.assertEqual(create_resp.status_code, 200)
            run = create_resp.json()["run"]
            self.assertEqual(run["trigger_source"], "immediate_create")
            self.assertTrue(run["task_id"])

            task_detail_resp = client.get(f"/api/tasks/{run['task_id']}")
            self.assertEqual(task_detail_resp.status_code, 200)
            task = task_detail_resp.json()["task"]
            self.assertEqual(task["launch_mode"], "immediate")
            self.assertEqual(task["latest_execution_id"], run["run_id"])

    def test_schedule_can_only_bind_deferred_task(self):
        task_payload = {
            "name": "零售立即执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-default",
            "repeat_count": 1,
            "launch_mode": "immediate",
        }
        schedule_payload = {
            "name": "每天早上巡检",
            "task_id": None,
            "schedule_type": "daily",
            "daily_time": "09:30",
            "schedule_status": "enabled",
        }
        with TestClient(app_module.app) as client:
            task_resp = client.post("/api/tasks", json=task_payload)
            self.assertEqual(task_resp.status_code, 200)
            schedule_payload["task_id"] = task_resp.json()["task"]["task_id"]

            schedule_resp = client.post("/api/schedules", json=schedule_payload)
            self.assertEqual(schedule_resp.status_code, 400)
            self.assertIn("deferred", schedule_resp.json()["detail"])

    def test_execute_deferred_task_creates_execution_history(self):
        payload = {
            "name": "零售待执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-default",
            "repeat_count": 1,
            "launch_mode": "deferred",
        }
        with TestClient(app_module.app) as client:
            create_resp = client.post("/api/tasks", json=payload)
            task_id = create_resp.json()["task"]["task_id"]

            first_execute = client.post(f"/api/tasks/{task_id}/execute")
            self.assertEqual(first_execute.status_code, 200)
            second_execute = client.post(f"/api/tasks/{task_id}/execute")
            self.assertEqual(second_execute.status_code, 200)

            detail_resp = client.get(f"/api/tasks/{task_id}")
            self.assertEqual(detail_resp.status_code, 200)
            detail = detail_resp.json()
            self.assertEqual(detail["task"]["task_status"], "running")
            self.assertEqual(len(detail["execution_history"]), 2)
            self.assertEqual(detail["latest_execution"]["run_id"], second_execute.json()["run"]["run_id"])

    def test_one_time_schedule_triggers_once(self):
        from backend.core.usecases.schedule_usecases import process_due_schedules

        task_payload = {
            "name": "零售待执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-default",
            "repeat_count": 1,
            "launch_mode": "deferred",
        }
        schedule_payload = {
            "name": "一次性巡检",
            "task_id": None,
            "schedule_type": "one_time",
            "run_at": "2026-03-18T09:30:00+08:00",
            "schedule_status": "enabled",
        }
        due_time = datetime(2026, 3, 18, 1, 30, tzinfo=timezone.utc)

        with TestClient(app_module.app) as client:
            task_resp = client.post("/api/tasks", json=task_payload)
            schedule_payload["task_id"] = task_resp.json()["task"]["task_id"]
            schedule_resp = client.post("/api/schedules", json=schedule_payload)
            self.assertEqual(schedule_resp.status_code, 200)
            schedule_id = schedule_resp.json()["schedule"]["schedule_id"]

            self.assertEqual(process_due_schedules(self.run_db, now=due_time), 1)
            self.assertEqual(process_due_schedules(self.run_db, now=due_time), 0)

            detail_resp = client.get(f"/api/tasks/{schedule_payload['task_id']}")
            self.assertEqual(detail_resp.status_code, 200)
            self.assertEqual(len(detail_resp.json()["execution_history"]), 1)

            schedule_detail = client.get(f"/api/schedules/{schedule_id}")
            self.assertEqual(schedule_detail.status_code, 200)
            self.assertEqual(schedule_detail.json()["schedule"]["schedule_status"], "completed")

    def test_daily_schedule_advances_next_triggered_at(self):
        from backend.core.usecases.schedule_usecases import process_due_schedules

        task_payload = {
            "name": "零售待执行任务",
            "case_set_id": "cs-nl2sql",
            "environment_id": "env-staging",
            "metric_set_id": "metric-default",
            "repeat_count": 1,
            "launch_mode": "deferred",
        }
        schedule_payload = {
            "name": "每日巡检",
            "task_id": None,
            "schedule_type": "daily",
            "daily_time": "09:30",
            "schedule_status": "enabled",
        }

        with TestClient(app_module.app) as client:
            task_resp = client.post("/api/tasks", json=task_payload)
            schedule_payload["task_id"] = task_resp.json()["task"]["task_id"]
            schedule_resp = client.post("/api/schedules", json=schedule_payload)
            self.assertEqual(schedule_resp.status_code, 200)
            schedule = schedule_resp.json()["schedule"]
            original_next = schedule["next_triggered_at"]

            processed = process_due_schedules(self.run_db, now=datetime.fromisoformat(original_next))
            self.assertEqual(processed, 1)

            refreshed_schedule = client.get(f"/api/schedules/{schedule['schedule_id']}")
            self.assertEqual(refreshed_schedule.status_code, 200)
            refreshed = refreshed_schedule.json()["schedule"]
            self.assertEqual(refreshed["schedule_status"], "enabled")
            self.assertNotEqual(refreshed["next_triggered_at"], original_next)
            self.assertTrue(refreshed["last_triggered_at"])


if __name__ == "__main__":
    unittest.main()
