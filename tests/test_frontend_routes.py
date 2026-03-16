import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from backend.app import app


class FrontendRouteTests(unittest.TestCase):
    def test_root_redirects_to_frontend(self):
        client = TestClient(app)
        response = client.get("/", follow_redirects=False)
        self.assertIn(response.status_code, (302, 307))
        self.assertEqual(response.headers.get("location"), "/frontend/")

    def test_frontend_index_served(self):
        client = TestClient(app)
        response = client.get("/frontend/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ChatBI 评测", response.text)


if __name__ == "__main__":
    unittest.main()
