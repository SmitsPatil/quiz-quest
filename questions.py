"""
Quiz Quest - Question Orchestrator Module
Manages Classic, AI, and Mixed modes with robust multi-tiered fallback:
Target API -> Secondary API -> Local Questions JSON.
Prevents duplicate questions and ensures 100% offline uptime.
"""

import json
import os
import random
from typing import Dict, Optional, List
from opentdb_api import get_opentdb_question, check_opentdb_status
from gemini_api import get_gemini_question, check_gemini_status

LOCAL_QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "questions.json")

# Level to difficulty mapping for progressive quest mode
LEVEL_DIFFICULTY_MAP = {
    1: "easy",
    2: "easy",
    3: "medium",
    4: "medium",
    5: "hard"
}


class QuestionManager:
    """Orchestrates question fetching across OpenTDB, Gemini AI, and Local Storage."""

    def __init__(self, mode: str = "mixed", category: str = "All Categories", difficulty: str = "medium"):
        self.mode = mode.lower()  # "classic", "ai", "mixed"
        self.category = category
        self.difficulty = difficulty
        self.mixed_turn = 0  # Alternates 0 (OpenTDB) and 1 (Gemini)
        self.seen_questions = set()  # Normalized questions seen in session
        self.local_questions = self._load_local_questions()

    def _load_local_questions(self) -> List[Dict]:
        """Load offline fallback questions from JSON file."""
        if not os.path.exists(LOCAL_QUESTIONS_FILE):
            return []
        try:
            with open(LOCAL_QUESTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[QuestionManager] Error loading local questions: {e}")
        return []

    def set_mode(self, mode: str):
        """Update active mode: 'classic', 'ai', or 'mixed'."""
        self.mode = mode.lower()

    def set_category(self, category: str):
        """Update chosen category."""
        self.category = category

    def set_difficulty(self, difficulty: str):
        """Update difficulty override (or None for level-based)."""
        self.difficulty = difficulty

    def reset_session(self):
        """Clear session cache for a fresh game run."""
        self.seen_questions.clear()
        self.mixed_turn = 0

    def get_difficulty_for_level(self, level: int) -> str:
        """Resolve difficulty based on level (1-5) or manual selection."""
        if self.difficulty and self.difficulty != "Progressive":
            return self.difficulty.lower()
        return LEVEL_DIFFICULTY_MAP.get(level, "medium")

    def get_next_question(self, level: int = 1) -> Dict:
        """
        Fetch the next question according to the selected mode with full fallback guarantees.
        Never returns None: if all APIs fail, returns from local storage.
        """
        diff = self.get_difficulty_for_level(level)
        cat = self.category

        question_data = None

        if self.mode == "classic":
            # Primary: OpenTDB -> Fallback: Gemini -> Fallback: Local
            question_data = self._fetch_opentdb(cat, diff)
            if not question_data:
                print("[QuestionManager] OpenTDB unavailable, attempting Gemini fallback...")
                question_data = self._fetch_gemini(cat, diff)

        elif self.mode == "ai":
            # Primary: Gemini -> Fallback: OpenTDB -> Fallback: Local
            question_data = self._fetch_gemini(cat, diff)
            if not question_data:
                print("[QuestionManager] Gemini unavailable, attempting OpenTDB fallback...")
                question_data = self._fetch_opentdb(cat, diff)

        else:  # "mixed" mode
            # Alternates between OpenTDB and Gemini
            if self.mixed_turn % 2 == 0:
                # Turn A: OpenTDB primary -> Gemini fallback
                question_data = self._fetch_opentdb(cat, diff)
                if not question_data:
                    question_data = self._fetch_gemini(cat, diff)
            else:
                # Turn B: Gemini primary -> OpenTDB fallback
                question_data = self._fetch_gemini(cat, diff)
                if not question_data:
                    question_data = self._fetch_opentdb(cat, diff)

            self.mixed_turn += 1

        # Final Fallback: If both APIs failed or network is down, load local question
        if not question_data:
            print("[QuestionManager] APIs unreachable. Engaging Local Quest Vault fallback.")
            question_data = self._get_local_question(cat, diff)

        # Record question as seen
        if question_data:
            self.seen_questions.add(self._normalize_text(question_data["question"]))

        return question_data

    def _normalize_text(self, text: str) -> str:
        """Normalize text for duplicate comparison."""
        return "".join(c.lower() for c in text if c.isalnum())

    def _is_duplicate(self, question_text: str) -> bool:
        """Check if question has already been asked this session."""
        return self._normalize_text(question_text) in self.seen_questions

    def _fetch_opentdb(self, category: str, difficulty: str) -> Optional[Dict]:
        """Fetch unique question from OpenTDB with retry on duplicates."""
        for _ in range(2):
            q = get_opentdb_question(category=category, difficulty=difficulty)
            if q and not self._is_duplicate(q["question"]):
                return q
        return None

    def _fetch_gemini(self, category: str, difficulty: str) -> Optional[Dict]:
        """Fetch unique question from Gemini AI with retry on duplicates."""
        for _ in range(2):
            q = get_gemini_question(category=category, difficulty=difficulty)
            if q and not self._is_duplicate(q["question"]):
                return q
        return None

    def _get_local_question(self, category: str, difficulty: str) -> Dict:
        """Fetch question from local questions bank, prioritizing category and difficulty."""
        if not self.local_questions:
            # Emergency fallback if file was deleted
            return {
                "question": "What is the speed of light in a vacuum (approximate)?",
                "options": ["300,000 km/s", "150,000 km/s", "30,000 km/s", "3,000 km/s"],
                "correct_answer": "300,000 km/s",
                "explanation": "Light travels at roughly 299,792 km/s through empty space.",
                "category": "Science",
                "difficulty": difficulty,
                "source": "Local Quest Vault"
            }

        # Filter by unseen first
        unseen = [q for q in self.local_questions if not self._is_duplicate(q["question"])]
        pool = unseen if unseen else self.local_questions

        # Filter by matching difficulty
        diff_pool = [q for q in pool if q.get("difficulty") == difficulty]
        candidates = diff_pool if diff_pool else pool

        selected = random.choice(candidates)

        # Clone and shuffle options to provide freshness
        options = list(selected["options"])
        random.shuffle(options)

        return {
            "question": selected["question"],
            "options": options,
            "correct_answer": selected["correct_answer"],
            "explanation": selected.get("explanation", f"'{selected['correct_answer']}' is the verified answer."),
            "category": selected.get("category", "General"),
            "difficulty": selected.get("difficulty", difficulty),
            "source": "Local Quest Vault"
        }

    def get_api_status(self) -> Dict[str, bool]:
        """Return connectivity status dictionary for UI display."""
        return {
            "opentdb": check_opentdb_status(),
            "gemini": check_gemini_status(),
            "local": len(self.local_questions) > 0
        }
