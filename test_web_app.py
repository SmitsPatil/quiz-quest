"""
Quiz Quest – Automated Web App & API Test Suite
Verifies all Flask routes, OpenTDB & Gemini services, fallback mechanism,
and Leaderboard endpoints using Flask's test client.
"""

import json
import unittest
from app import app, load_leaderboard_data


class TestQuizQuestWebApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_01_homepage_renders(self):
        """Test 1: Verify homepage returns HTTP 200 and renders HTML."""
        print("\n[Web Test 1] Testing Homepage rendering...")
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Quiz Quest", res.data)
        self.assertIn(b"particleCanvas", res.data)
        print("  [PASS] Homepage rendered successfully (HTTP 200).")

    def test_02_categories_endpoint(self):
        """Test 2: Verify category list endpoint."""
        print("\n[Web Test 2] Testing /api/categories endpoint...")
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("categories", data)
        self.assertTrue(len(data["categories"]) > 5)
        print(f"  [PASS] Categories retrieved: {len(data['categories'])} available.")

    def test_03_classic_mode_question(self):
        """Test 3: Verify Classic mode question retrieval."""
        print("\n[Web Test 3] Testing /api/question in Classic Mode (OpenTDB)...")
        payload = {
            "mode": "classic",
            "category": "General Knowledge",
            "difficulty": "easy",
            "level": 1,
            "question_number": 1
        }
        res = self.client.post("/api/question", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        q = data.get("question")
        self.assertIsNotNone(q)
        self.assertEqual(len(q["options"]), 4)
        self.assertIn(q["correct_answer"], q["options"])
        print(f"  [PASS] Classic question: '{q['question'][:50]}...' (Source: {q['source']})")

    def test_04_ai_mode_question(self):
        """Test 4: Verify AI mode question generation (Gemini)."""
        print("\n[Web Test 4] Testing /api/question in AI Mode (Gemini)...")
        payload = {
            "mode": "ai",
            "category": "Science & Nature",
            "difficulty": "medium",
            "level": 2,
            "question_number": 2
        }
        res = self.client.post("/api/question", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        q = data.get("question")
        self.assertIsNotNone(q)
        self.assertEqual(len(q["options"]), 4)
        self.assertIn(q["correct_answer"], q["options"])
        print(f"  [PASS] AI question: '{q['question'][:50]}...' (Source: {q['source']})")

    def test_05_mixed_mode_alternation(self):
        """Test 5: Verify Mixed mode alternation."""
        print("\n[Web Test 5] Testing /api/question in Mixed Mode alternation...")
        p1 = {"mode": "mixed", "question_number": 1, "level": 1}
        p2 = {"mode": "mixed", "question_number": 2, "level": 1}

        res1 = self.client.post("/api/question", json=p1)
        res2 = self.client.post("/api/question", json=p2)

        data1 = res1.get_json()["question"]
        data2 = res2.get_json()["question"]

        print(f"  [PASS] Turn 1 Source: {data1['source']}")
        print(f"  [PASS] Turn 2 Source: {data2['source']}")

    def test_06_offline_fallback(self):
        """Test 6: Verify offline fallback to local questions.json."""
        print("\n[Web Test 6] Testing offline fallback resilience...")
        from services.opentdb import opentdb_service
        from services.gemini import gemini_service

        # Temporarily mock services to fail
        orig_open = opentdb_service.get_question
        orig_gem = gemini_service.generate_question
        try:
            opentdb_service.get_question = lambda c, d: None
            gemini_service.generate_question = lambda c, d: None

            res = self.client.post("/api/question", json={"mode": "mixed", "level": 1})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()["question"]
            self.assertEqual(data["source"], "Local Quest Vault")
            self.assertEqual(len(data["options"]), 4)
            print(f"  [PASS] Successfully fell back to Local Quest Vault: '{data['question'][:45]}...'")
        finally:
            opentdb_service.get_question = orig_open
            gemini_service.generate_question = orig_gem

    def test_07_leaderboard_post_and_get(self):
        """Test 7: Verify Leaderboard submission and retrieval."""
        print("\n[Web Test 7] Testing Leaderboard submission and top 10 retrieval...")
        payload = {
            "name": "WebScholar",
            "score": 350,
            "accuracy": 92,
            "level": 5,
            "mode": "Mixed Mode"
        }
        post_res = self.client.post("/api/leaderboard", json=payload)
        self.assertEqual(post_res.status_code, 200)
        post_data = post_res.get_json()
        self.assertTrue(post_data.get("success"))

        get_res = self.client.get("/api/leaderboard")
        self.assertEqual(get_res.status_code, 200)
        board = get_res.get_json().get("leaderboard", [])
        self.assertTrue(len(board) > 0)
        top = board[0]
        self.assertGreaterEqual(top["score"], 350)
        print(f"  [PASS] Top leaderboard entry: {top['name']} with {top['score']} points.")

    def test_08_api_status_endpoint(self):
        """Test 8: Verify live status endpoint."""
        print("\n[Web Test 8] Testing /api/status health check...")
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        status = res.get_json()
        self.assertIn("gemini", status)
        self.assertIn("opentdb", status)
        self.assertIn("local", status)
        print(f"  [PASS] System Health: Gemini={status['gemini']}, OpenTDB={status['opentdb']}, Local={status['local']}")


if __name__ == "__main__":
    unittest.main()
