"""
Quiz Quest - Open Trivia Database (OpenTDB) API Client
Handles batch fetching, HTML unescaping, answer shuffling, category/difficulty filtering,
and robust network/API error handling.
"""

import html
import json
import random
import time
import urllib.parse
import urllib.request
import urllib.error

# Map friendly category names to OpenTDB category IDs
OPENTDB_CATEGORIES = {
    "All Categories": None,
    "General Knowledge": 9,
    "Entertainment: Film": 11,
    "Entertainment: Music": 12,
    "Science & Nature": 17,
    "Computers & Tech": 18,
    "Mythology": 20,
    "Sports": 21,
    "Geography": 22,
    "History": 23
}


class OpenTDBClient:
    """Client for fetching and caching questions from the Open Trivia Database."""

    def __init__(self, timeout: float = 5.0):
        self.base_url = "https://opentdb.com/api.php"
        self.timeout = timeout
        self.batch_cache = []  # In-memory batch queue of questions
        self.last_fetch_time = 0.0
        self.rate_limit_delay = 5.0  # OpenTDB rate-limits if polled faster than 5 seconds

    def _build_url(self, amount: int = 10, category_name: str = None, difficulty: str = None) -> str:
        """Construct query URL with parameters."""
        params = {
            "amount": amount,
            "type": "multiple"
        }

        if category_name and category_name in OPENTDB_CATEGORIES:
            cat_id = OPENTDB_CATEGORIES[category_name]
            if cat_id is not None:
                params["category"] = cat_id

        if difficulty and difficulty.lower() in ["easy", "medium", "hard"]:
            params["difficulty"] = difficulty.lower()

        return f"{self.base_url}?{urllib.parse.urlencode(params)}"

    def fetch_batch(self, amount: int = 10, category_name: str = None, difficulty: str = None) -> list:
        """
        Fetch a batch of questions from OpenTDB.
        Returns a list of standardized question dicts, or empty list on failure.
        """
        # Respect OpenTDB rate-limiting
        elapsed = time.time() - self.last_fetch_time
        if elapsed < self.rate_limit_delay and self.last_fetch_time > 0:
            time.sleep(self.rate_limit_delay - elapsed)

        url = self._build_url(amount=amount, category_name=category_name, difficulty=difficulty)
        headers = {
            "User-Agent": "QuizQuest/1.0 (Educational Pygame Project)"
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            self.last_fetch_time = time.time()
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            code = data.get("response_code", -1)
            # Response Codes:
            # 0: Success
            # 1: No Results
            # 2: Invalid Parameter
            # 3: Token Not Found
            # 4: Token Empty
            # 5: Rate Limit
            if code != 0:
                print(f"[OpenTDB] API returned non-zero code {code} (1=NoResults, 5=RateLimit)")
                # If category had no results, retry without category
                if code == 1 and category_name and category_name != "All Categories":
                    return self.fetch_batch(amount=amount, category_name=None, difficulty=difficulty)
                return []

            raw_results = data.get("results", [])
            questions = []
            for item in raw_results:
                clean_q = self._normalize_question(item)
                if clean_q:
                    questions.append(clean_q)

            return questions

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"[OpenTDB] Network / HTTP error: {e}")
            return []
        except Exception as e:
            print(f"[OpenTDB] Unexpected error: {e}")
            return []

    def _normalize_question(self, item: dict) -> dict:
        """Clean HTML entities and structure question dictionary."""
        try:
            question_text = html.unescape(item["question"]).strip()
            correct_ans = html.unescape(item["correct_answer"]).strip()
            incorrect_ans = [html.unescape(ans).strip() for ans in item["incorrect_answers"]]

            # Combine and shuffle options
            options = [correct_ans] + incorrect_ans
            random.shuffle(options)

            # Generate default explanation
            explanation = f"'{correct_ans}' is the verified answer according to the Open Trivia Database."

            return {
                "question": question_text,
                "options": options,
                "correct_answer": correct_ans,
                "explanation": explanation,
                "category": html.unescape(item.get("category", "General")),
                "difficulty": item.get("difficulty", "medium"),
                "source": "Open Trivia DB"
            }
        except KeyError as e:
            print(f"[OpenTDB] Malformed item missing key: {e}")
            return None

    def get_question(self, category_name: str = None, difficulty: str = None) -> dict:
        """
        Get a single question. Uses cached batch if available; otherwise fetches a new batch.
        """
        # If cache has items, pop one
        if self.batch_cache:
            return self.batch_cache.pop(0)

        # Refill batch
        new_batch = self.fetch_batch(amount=10, category_name=category_name, difficulty=difficulty)
        if new_batch:
            self.batch_cache.extend(new_batch)
            return self.batch_cache.pop(0)

        return None


# Module-level singleton
_opentdb_client = OpenTDBClient()


def get_opentdb_question(category: str = None, difficulty: str = None) -> dict:
    """Helper function to fetch a single question from OpenTDB."""
    return _opentdb_client.get_question(category_name=category, difficulty=difficulty)


def check_opentdb_status() -> bool:
    """Quick status check for OpenTDB connectivity."""
    try:
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        req = urllib.request.Request(url, headers={"User-Agent": "QuizQuest/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response_code") == 0
    except Exception:
        return False
