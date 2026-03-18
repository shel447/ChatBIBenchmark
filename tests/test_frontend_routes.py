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
        self.assertIn("环境配置", response.text)
        self.assertIn("指标管理", response.text)
        self.assertIn("导入用例", response.text)
        self.assertIn("新增评测", response.text)
        self.assertIn("用例集", response.text)
        self.assertIn("用例列表", response.text)
        self.assertIn("用例详情", response.text)
        self.assertIn("启动时间", response.text)
        self.assertIn("结束时间", response.text)
        self.assertIn("指标参数集", response.text)
        self.assertIn("进展", response.text)
        self.assertIn("准确率", response.text)
        self.assertIn("用例集执行次数", response.text)
        self.assertIn("创建评测任务", response.text)
        self.assertIn("创建并启动", response.text)
        self.assertIn("任务名称", response.text)
        self.assertIn("进度条", response.text)
        self.assertIn("导出用例集", response.text)
        self.assertIn("导出所选", response.text)
        self.assertIn("更新用例集", response.text)
        self.assertIn("用例工具", response.text)
        self.assertIn("扩增用例集", response.text)
        self.assertIn("种子", response.text)
        self.assertIn("不可评测", response.text)
        self.assertNotIn("用例集与用例工具", response.text)
        self.assertNotIn("<h2>用例集</h2>", response.text)
        self.assertNotIn("primary-nav", response.text)


if __name__ == "__main__":
    unittest.main()
