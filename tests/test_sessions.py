import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

import main


class SessionIsolationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        key_patch = patch.object(main, "DEEPSEEK_API_KEY", "test-key")
        key_patch.start()
        self.addCleanup(key_patch.stop)
        path_patch = patch.object(
            main,
            "get_session_file_name",
            side_effect=lambda session_id: os.path.join(
                self.directory.name, f"{session_id}.json"
            ),
        )
        path_patch.start()
        self.addCleanup(path_patch.stop)
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="新谜面"))]
        )
        model_patch = patch.object(
            main.client.chat.completions, "create", return_value=response
        )
        model_patch.start()
        self.addCleanup(model_patch.stop)

    def test_visitors_have_separate_persistent_sessions(self):
        first = TestClient(main.app)
        second = TestClient(main.app)

        first_session = first.get("/api/session").json()["data"]
        second_session = second.get("/api/session").json()["data"]
        first_id = first.cookies.get(main.COOKIE_NAME)
        second_id = second.cookies.get(main.COOKIE_NAME)
        self.assertNotEqual(first_id, second_id)
        self.assertNotIn("current_session", first_session)
        self.assertEqual(first.get("/api/session").json()["data"], first_session)

        result = first.post(
            "/api/chat",
            json={"message": "你好", "session_id": second_id},
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(first.get("/api/session").json()["data"]["message"]), 2)
        self.assertEqual(second.get("/api/session").json()["data"]["message"], [])

    def test_chat_requires_existing_cookie(self):
        response = TestClient(main.app).post("/api/chat", json={"message": "你好"})
        self.assertEqual(response.status_code, 401)

    def test_new_visitor_cannot_inherit_legacy_session(self):
        legacy_path = os.path.join(self.directory.name, "20260520_142726.json")
        with open(legacy_path, "w", encoding="utf-8") as file:
            json.dump({"current_session": "20260520_142726", "message": ["private"]}, file)

        result = TestClient(main.app).get("/api/session")
        self.assertEqual(result.json()["data"]["message"], [])
        self.assertNotIn("current_session", result.json()["data"])
        self.assertIn("httponly", result.headers["set-cookie"].lower())
        self.assertEqual(result.headers["cache-control"], "private, no-store")


if __name__ == "__main__":
    unittest.main()
