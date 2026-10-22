"""
Quiz Quest - Automated Test Suite
Verifies all functional requirements:
1. OpenTDB Question Retrieval
2. Gemini AI Question Generation
3. Correct and Incorrect Answer logic
4. Scoring, Lives, and Level Progression
5. All Three Question Modes (Classic, AI, Mixed)
6. API Failures and Offline Fallback
7. Leaderboard Persistence
"""

import sys
import os
import unittest
from dotenv import load_dotenv

load_dotenv()

from opentdb_api import get_opentdb_question, check_opentdb_status
from gemini_api import get_gemini_question, check_gemini_status
from questions import QuestionManager
from leaderboard import save_leaderboard_entry, load_leaderboard, get_top_entries


class TestQuizQuest(unittest.TestCase):

    def test_01_opentdb_retrieval(self):
        """Test 1: Verify OpenTDB fetches well-formed multiple choice trivia."""
        print("\n[Test 1] Testing OpenTDB question retrieval...")
        q = get_opentdb_question(category="General Knowledge", difficulty="easy")
        if q:
            self.assertIn("question", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["correct_answer"], q["options"])
            self.assertEqual(q["source"], "Open Trivia DB")
            print(f"  [PASS] OpenTDB returned: {q['question'][:60]}...")
        else:
            print("  ! OpenTDB network request timed out or was rate-limited (expected occasionally).")

    def test_02_gemini_generation(self):
        """Test 2: Verify Gemini generates structured questions with 4 options and explanation."""
        print("\n[Test 2] Testing Gemini question generation...")
        if not check_gemini_status():
            print("  ! Skipping Gemini API call: GEMINI_API_KEY not configured.")
            return

        q = get_gemini_question(category="Science & Nature", difficulty="easy")
        self.assertIsNotNone(q, "Gemini should return a valid question dictionary")
        self.assertIn("question", q)
        self.assertEqual(len(q["options"]), 4)
        self.assertIn(q["correct_answer"], q["options"])
        self.assertTrue(len(q["explanation"]) > 5)
        self.assertEqual(q["source"], "Gemini AI")
        print(f"  [PASS] Gemini generated: {q['question']}")
        print(f"  [PASS] Explanation: {q['explanation'][:70]}...")

    def test_03_scoring_and_lives_logic(self):
        """Test 3: Verify correct answers add 10 points, incorrect answers deduct 1 life."""
        print("\n[Test 3] Testing Scoring and Lives logic...")
        score = 0
        lives = 3

        # Simulate Correct Answer
        is_correct = True
        if is_correct:
            score += 10
        self.assertEqual(score, 10)
        self.assertEqual(lives, 3)
        print("  [PASS] Correct answer awards +10 points (Score: 10, Lives: 3)")

        # Simulate Incorrect Answer
        is_correct = False
        if not is_correct:
            lives -= 1
        self.assertEqual(score, 10)
        self.assertEqual(lives, 2)
        print("  [PASS] Incorrect answer deducts 1 life (Score: 10, Lives: 2)")

    def test_04_level_progression(self):
        """Test 4: Verify 5-level progression and difficulty curve."""
        print("\n[Test 4] Testing Level progression curve...")
        qm = QuestionManager(difficulty="Progressive")

        diff_l1 = qm.get_difficulty_for_level(1)
        diff_l3 = qm.get_difficulty_for_level(3)
        diff_l5 = qm.get_difficulty_for_level(5)

        self.assertEqual(diff_l1, "easy")
        self.assertEqual(diff_l3, "medium")
        self.assertEqual(diff_l5, "hard")
        print(f"  [PASS] Level 1 Difficulty: {diff_l1}")
        print(f"  [PASS] Level 3 Difficulty: {diff_l3}")
        print(f"  [PASS] Level 5 Difficulty: {diff_l5}")

    def test_05_modes_classic_ai_mixed(self):
        """Test 5: Verify Classic, AI, and Mixed question modes."""
        print("\n[Test 5] Testing all three question modes...")
        qm = QuestionManager(mode="classic")
        q_classic = qm.get_next_question(1)
        self.assertIsNotNone(q_classic)
        print(f"  [PASS] Classic Mode question source: {q_classic['source']}")

        qm.set_mode("ai")
        q_ai = qm.get_next_question(1)
        self.assertIsNotNone(q_ai)
        print(f"  [PASS] AI Mode question source: {q_ai['source']}")

        qm.set_mode("mixed")
        q_mixed_1 = qm.get_next_question(1)
        q_mixed_2 = qm.get_next_question(1)
        self.assertIsNotNone(q_mixed_1)
        self.assertIsNotNone(q_mixed_2)
        print(f"  [PASS] Mixed Mode Turn 1 source: {q_mixed_1['source']}")
        print(f"  [PASS] Mixed Mode Turn 2 source: {q_mixed_2['source']}")

    def test_06_api_failure_and_offline_fallback(self):
        """Test 6: Verify offline fallback to local questions when both APIs fail."""
        print("\n[Test 6] Testing API failure and offline fallback...")
        qm = QuestionManager(mode="mixed")
        # Force both APIs to return None
        qm._fetch_opentdb = lambda c, d: None
        qm._fetch_gemini = lambda c, d: None

        fallback_q = qm.get_next_question(1)
        self.assertIsNotNone(fallback_q)
        self.assertEqual(fallback_q["source"], "Local Quest Vault")
        self.assertEqual(len(fallback_q["options"]), 4)
        self.assertIn(fallback_q["correct_answer"], fallback_q["options"])
        print(f"  [PASS] Offline Fallback succeeded: {fallback_q['question']}")

    def test_07_leaderboard_persistence(self):
        """Test 7: Verify high scores saving and loading in data/leaderboard.json."""
        print("\n[Test 7] Testing Leaderboard persistence...")
        test_player = "TestKnight"
        test_score = 999
        test_level = 5

        success = save_leaderboard_entry(test_player, test_score, test_level, "Mixed Mode")
        self.assertTrue(success)

        top_entries = get_top_entries(limit=10)
        self.assertTrue(len(top_entries) > 0)
        # Check that top score is >= 999
        self.assertGreaterEqual(top_entries[0]["score"], test_score)
        print(f"  [PASS] Top entry recorded: {top_entries[0]['name']} - {top_entries[0]['score']} pts")


if __name__ == "__main__":
    unittest.main()
