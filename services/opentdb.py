"""
Quiz Quest - Open Trivia Database (OpenTDB) Service
Handles HTTP requests, batch caching, HTML unescaping, and rate-limit handling.
"""

import html
import json
import random
import time
import urllib.parse
import urllib.request
import urllib.error

# OpenTDB category mapping
OPENTDB_CATEGORIES = {
    "All Categories": None,
    "General Knowledge": 9,
    "Entertainment: Books": 10,
    "Entertainment: Film": 11,
    "Entertainment: Music": 12,
    "Entertainment: Video Games": 15,
    "Science & Nature": 17,
    "Computers & Tech": 18,
    "Mythology": 20,
    "Sports": 21,
    "Geography": 22,
    "History": 23
}


class OpenTDBService:
    """Service to fetch trivia questions from OpenTDB with in-memory batch caching."""

    def __init__(self, timeout: float = 6.0):
        self.base_url = "https://opentdb.com/api.php"
        self.timeout = timeout
        self.batch_cache = []
        self.last_fetch_time = 0.0
        self.rate_limit_delay = 5.0

    def _build_url(self, amount: int = 10, category: str = None, difficulty: str = None) -> str:
        params = {"amount": amount, "type": "multiple"}

        if category and category in OPENTDB_CATEGORIES:
            cat_id = OPENTDB_CATEGORIES[category]
            if cat_id is not None:
                params["category"] = cat_id

        if difficulty and difficulty.lower() in ["easy", "medium", "hard"]:
            params["difficulty"] = difficulty.lower()

        return f"{self.base_url}?{urllib.parse.urlencode(params)}"

    def fetch_batch(self, amount: int = 10, category: str = None, difficulty: str = None) -> list:
        """Fetch questions batch from OpenTDB with rate limit safety."""
        elapsed = time.time() - self.last_fetch_time
        if elapsed < self.rate_limit_delay and self.last_fetch_time > 0:
            time.sleep(self.rate_limit_delay - elapsed)

        url = self._build_url(amount=amount, category=category, difficulty=difficulty)
        headers = {"User-Agent": "QuizQuestWeb/1.0 (College Educational Project)"}

        try:
            req = urllib.request.Request(url, headers=headers)
            self.last_fetch_time = time.time()
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            code = data.get("response_code", -1)
            if code != 0:
                print(f"[OpenTDB] Non-zero response code: {code}")
                # If category returned no results, retry with general
                if code == 1 and category and category != "All Categories":
                    return self.fetch_batch(amount=amount, category=None, difficulty=difficulty)
                return []

            results = []
            for item in data.get("results", []):
                q = self._normalize_question(item)
                if q:
                    results.append(q)
            return results

        except Exception as e:
            print(f"[OpenTDB] Fetch error: {e}")
            return []

    def _normalize_question(self, item: dict) -> dict:
        """Clean HTML entities and structure multiple choice question."""
        try:
            question_text = html.unescape(item["question"]).strip()
            correct_ans = html.unescape(item["correct_answer"]).strip()
            incorrect_ans = [html.unescape(ans).strip() for ans in item["incorrect_answers"]]

            options = [correct_ans] + incorrect_ans
            random.shuffle(options)

            explanation = f"'{correct_ans}' is the verified answer from the Open Trivia Database."

            return {
                "question": question_text,
                "options": options,
                "correct_answer": correct_ans,
                "explanation": explanation,
                "category": html.unescape(item.get("category", "General Knowledge")),
                "difficulty": item.get("difficulty", "medium"),
                "source": "Open Trivia DB"
            }
        except Exception as e:
            print(f"[OpenTDB] Normalization error: {e}")
            return None

    def get_question(self, category: str = None, difficulty: str = None) -> dict:
        """Retrieve a single question from batch queue or fetch fresh batch."""
        if self.batch_cache:
            return self.batch_cache.pop(0)

        new_batch = self.fetch_batch(amount=10, category=category, difficulty=difficulty)
        if new_batch:
            self.batch_cache.extend(new_batch)
            return self.batch_cache.pop(0)

        return None

    def check_health(self) -> bool:
        """Ping OpenTDB API to verify connectivity."""
        try:
            req = urllib.request.Request("https://opentdb.com/api.php?amount=1&type=multiple",
                                         headers={"User-Agent": "QuizQuestWeb/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response_code") == 0
        except Exception:
            return False


# Singleton instance
opentdb_service = OpenTDBService()
