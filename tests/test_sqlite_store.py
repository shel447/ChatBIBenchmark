import os
import sys
import sqlite3
import unittest
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
TMP_DIR = os.path.join(ROOT, "tests", ".tmp")

sys.path.insert(0, BACKEND)

from storage import sqlite_store


class SQLiteStoreTests(unittest.TestCase):
    def test_save_and_list_runs(self):
        os.makedirs(TMP_DIR, exist_ok=True)
        db_path = os.path.join(TMP_DIR, f"store-{uuid.uuid4().hex}.db")
        try:
            sqlite_store.init_db(db_path)
            sqlite_store.save_run(db_path, "run-1", {"n_turns": 5}, {"overall": 0.8})
            run = sqlite_store.get_run(db_path, "run-1")
            self.assertEqual(run["run_id"], "run-1")
            self.assertEqual(run["config"]["n_turns"], 5)

            runs = sqlite_store.list_runs(db_path, limit=10)
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["run_id"], "run-1")
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_save_case_result(self):
        os.makedirs(TMP_DIR, exist_ok=True)
        db_path = os.path.join(TMP_DIR, f"case-{uuid.uuid4().hex}.db")
        try:
            sqlite_store.init_db(db_path)
            sqlite_store.save_case_result(
                db_path,
                "run-1",
                "case-1",
                {"score": 0.9},
                {"details": "ok"},
            )
            conn = sqlite3.connect(db_path)
            cur = conn.execute(
                "select run_id, case_id from report_case_result where run_id = ?",
                ("run-1",),
            )
            row = cur.fetchone()
            conn.close()
            self.assertEqual(row[0], "run-1")
            self.assertEqual(row[1], "case-1")
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == "__main__":
    unittest.main()
