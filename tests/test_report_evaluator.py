import os
import sys
import tempfile
import unittest
import sqlite3
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
TMP_DIR = os.path.join(ROOT, "tests", ".tmp")

sys.path.insert(0, BACKEND)

from core import evaluator
from adapters.sqlite_adapter import SQLiteAdapter


class ReportEvaluatorTests(unittest.TestCase):
    def test_template_accuracy_top1_topk(self):
        metrics = evaluator.score_template(
            expected_template_id="t1",
            predicted_template_id="t1",
            predicted_ranked_ids=["t1", "t2", "t3"],
            k=3,
        )
        self.assertEqual(metrics["top1"], 1.0)
        self.assertEqual(metrics["topk"], 1.0)

        metrics = evaluator.score_template(
            expected_template_id="t1",
            predicted_template_id="t2",
            predicted_ranked_ids=["t2", "t3", "t1"],
            k=3,
        )
        self.assertEqual(metrics["top1"], 0.0)
        self.assertEqual(metrics["topk"], 1.0)

    def test_param_precision_recall_f1(self):
        ground_truth = {
            "date_range": {
                "type": "date_range",
                "value": {"start": "2025-01-01", "end": "2025-01-31"},
            },
            "region": {"type": "enum", "value": "east"},
            "metric": {"type": "enum", "value": "gmv"},
        }
        filled_params = {
            "region": {"type": "enum", "value": "East"},
            "metric": {"type": "enum", "value": "gmv"},
        }
        metrics = evaluator.score_params(ground_truth, filled_params)
        self.assertAlmostEqual(metrics["precision"], 1.0)
        self.assertAlmostEqual(metrics["recall"], 2.0 / 3.0)
        self.assertAlmostEqual(metrics["f1"], 0.8, places=2)

    def test_completion_within_n_turns(self):
        missing_by_turn = [["date_range", "region"], ["date_range"], []]
        result = evaluator.score_completion(missing_by_turn, n_turns=3)
        self.assertTrue(result["completed"])
        self.assertEqual(result["turns_used"], 3)

        result = evaluator.score_completion(missing_by_turn, n_turns=2)
        self.assertFalse(result["completed"])
        self.assertEqual(result["turns_used"], 2)

    def test_outline_f1(self):
        expected = {
            "title": "Report",
            "sections": [
                {"title": "Overview", "sections": []},
                {"title": "Sales", "sections": [{"title": "By Region", "sections": []}]},
            ],
        }
        actual = {
            "title": "Report",
            "sections": [{"title": "Overview", "sections": []}],
        }
        metrics = evaluator.score_outline(expected, actual)
        self.assertAlmostEqual(metrics["precision"], 1.0)
        self.assertAlmostEqual(metrics["recall"], 0.5)
        self.assertAlmostEqual(metrics["f1"], 0.666, places=2)

    def test_content_assertions_with_sqlite_adapter(self):
        os.makedirs(TMP_DIR, exist_ok=True)
        db_path = os.path.join(TMP_DIR, f"test-{uuid.uuid4().hex}.db")
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("create table sales(region text, amount integer)")
            cur.executemany(
                "insert into sales(region, amount) values (?, ?)",
                [("east", 100), ("west", 150)],
            )
            conn.commit()
            conn.close()

            adapter = SQLiteAdapter(db_path)
            assertions = [
                {
                    "statement_id": "s1",
                    "sql": "select sum(amount) from sales",
                    "expected_value": 250,
                    "tolerance": 0,
                },
                {
                    "statement_id": "s2",
                    "sql": "select count(*) from sales where region = 'east'",
                    "expected_value": 1,
                    "tolerance": 0,
                },
            ]
            report_facts = {"s1": 250, "s2": 1}
            metrics = evaluator.score_content_assertions(
                assertions, report_facts, adapter
            )
            self.assertAlmostEqual(metrics["pass_rate"], 1.0)
            self.assertAlmostEqual(metrics["fail_rate"], 0.0)
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == "__main__":
    unittest.main()
