import io
import os
import sys
import tempfile
import unittest

from openpyxl import Workbook, load_workbook

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import backend.app as app_module
from fastapi.testclient import TestClient


class CaseSetApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.meta_db = os.path.join(self.tmp_dir.name, "report_eval.db")
        self.run_db = os.path.join(self.tmp_dir.name, "runs.db")
        self.case_set_db = os.path.join(self.tmp_dir.name, "case_sets.db")
        app_module.DEFAULT_META_DB = self.meta_db
        app_module.DEFAULT_RUN_DB = self.run_db
        app_module.DEFAULT_CASE_SET_DB = self.case_set_db

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_list_case_sets(self):
        with TestClient(app_module.app) as client:
            response = client.get("/api/case-sets")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("case_sets", data)
            self.assertTrue(any(item["id"] == "cs-nl2sql" for item in data["case_sets"]))

    def test_export_case_set_returns_excel(self):
        with TestClient(app_module.app) as client:
            response = client.get("/api/case-sets/cs-nl2sql/export")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers["content-type"],
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            workbook = load_workbook(io.BytesIO(response.content))
            sheet = workbook.active
            headers = [cell.value for cell in sheet[1]]
            self.assertEqual(headers, ["case_id", "question", "expected_sql"])
            self.assertEqual(sheet["A2"].value, "NL2SQL-014")

    def test_import_case_set_overwrites_existing_cases(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["case_id", "question", "expected_sql"])
        sheet.append(["NL2SQL-999", "本月 GMV", "SELECT sum(gmv) FROM sales"])
        content = io.BytesIO()
        workbook.save(content)
        content.seek(0)

        with TestClient(app_module.app) as client:
            response = client.post(
                "/api/case-sets/cs-nl2sql/import",
                files={"file": ("cs-nl2sql.xlsx", content.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            self.assertEqual(response.status_code, 200)

            detail = client.get("/api/case-sets/cs-nl2sql")
            self.assertEqual(detail.status_code, 200)
            payload = detail.json()
            self.assertEqual(len(payload["cases"]), 1)
            self.assertEqual(payload["cases"][0]["case_id"], "NL2SQL-999")

    def test_import_rejects_invalid_template(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["case_id", "question", "wrong_column"])
        content = io.BytesIO()
        workbook.save(content)
        content.seek(0)

        with TestClient(app_module.app) as client:
            response = client.post(
                "/api/case-sets/cs-nl2sql/import",
                files={"file": ("invalid.xlsx", content.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("template", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
