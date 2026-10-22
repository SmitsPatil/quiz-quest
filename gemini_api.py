"""
Quiz Quest - Google Gemini AI API Client
Handles question generation, structured JSON validation, answer explanations,
and fallback across compatible Gemini models.
"""

import json
import os
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# List of compatible models to attempt in priority order
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3-flash-preview"
]


class GeminiClient:
    """Client for generating quiz questions and explanations using Google Gemini API."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self._init_sdk()
        self.batch_cache = []

    def _init_sdk(self):
        """Initialize the modern google.genai Client."""
        if not self.api_key:
            return
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"[Gemini] Failed to initialize Google GenAI SDK: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Gemini client is properly configured with an API key."""
        return bool(self.api_key and self.client)

    def generate_question(self, category: str = "General Knowledge", difficulty: str = "medium") -> dict:
        """
        Generate a single multiple-choice question using Gemini.
        Returns validated question dictionary or None on failure.
        """
        if self.batch_cache:
            return self.batch_cache.pop(0)

        # Generate a small batch (3 questions) to keep UI snappy
        batch = self.generate_batch(amount=3, category=category, difficulty=difficulty)
        if batch:
            self.batch_cache.extend(batch)
            return self.batch_cache.pop(0)

        return None

    def generate_batch(self, amount: int = 3, category: str = "General Knowledge", difficulty: str = "medium") -> list:
        """
        Request a batch of structured trivia questions in JSON format.
        """
        if not self.is_available():
            # Refresh key in case .env was modified at runtime
            self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
            self._init_sdk()
            if not self.is_available():
                return []

        from google.genai import types

        cat_str = category if category and category != "All Categories" else "General Knowledge, Science, History, or Pop Culture"
        diff_str = difficulty if difficulty else "medium"

        prompt = (
            f"You are a master trivia architect for an adventure quiz game.\n"
            f"Generate exactly {amount} engaging multiple-choice trivia questions.\n"
            f"Category focus: {cat_str}.\n"
            f"Difficulty level: {diff_str} (easy for newcomers, medium for enthusiasts, hard for masters).\n\n"
            f"Strict Output Format:\n"
            f"Return ONLY a JSON array containing objects with these exact keys:\n"
            f"- question: (string) clear, concise trivia question\n"
            f"- options: (array of 4 unique strings) one correct answer and three plausible distractors\n"
            f"- correct_answer: (string) exactly matching one of the options\n"
            f"- explanation: (string) 1-2 sentence fascinating explanation of why the correct answer is true"
        )

        # Try candidate models with graceful fallback
        for model_name in CANDIDATE_MODELS:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                        max_output_tokens=1500,
                        http_options=types.HttpOptions(timeout=15000)
                    )
                )

                raw_text = response.text.strip()
                parsed = self._parse_and_validate_batch(raw_text, category, diff_str)
                if parsed:
                    return parsed
            except Exception as e:
                err_str = str(e)
                print(f"[Gemini] Model '{model_name}' encountered error: {err_str[:120]}...")
                # Continue loop to try next candidate model

        return []

    def _parse_and_validate_batch(self, raw_json_str: str, category: str, difficulty: str) -> list:
        """Parse raw JSON string and strictly validate schema."""
        try:
            data = json.loads(raw_json_str)
            # Handle if model wrapped in a single object {"questions": [...]}
            if isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        data = val
                        break
                else:
                    data = [data]

            valid_questions = []
            for item in data:
                clean_q = self._validate_question_dict(item, category, difficulty)
                if clean_q:
                    valid_questions.append(clean_q)

            return valid_questions
        except json.JSONDecodeError as e:
            print(f"[Gemini] JSON parse error: {e}")
            return []

    def _validate_question_dict(self, item: dict, default_category: str, difficulty: str) -> dict:
        """Ensure question meets all constraints."""
        if not isinstance(item, dict):
            return None

        question = str(item.get("question", "")).strip()
        options = item.get("options")
        correct_answer = str(item.get("correct_answer", "")).strip()
        explanation = str(item.get("explanation", "")).strip()

        if not question or not correct_answer:
            return None

        if not isinstance(options, list) or len(options) != 4:
            return None

        # Clean string options and deduplicate check
        cleaned_options = [str(opt).strip() for opt in options]
        if len(set(cleaned_options)) != 4:
            return None

        # Verify correct_answer matches one of options
        if correct_answer not in cleaned_options:
            # Check case-insensitive match
            matches = [opt for opt in cleaned_options if opt.lower() == correct_answer.lower()]
            if matches:
                correct_answer = matches[0]
            else:
                return None

        # Shuffle options so correct answer is not in predictable spot
        shuffled = list(cleaned_options)
        random.shuffle(shuffled)

        if not explanation:
            explanation = f"'{correct_answer}' is verified by Gemini AI knowledge."

        return {
            "question": question,
            "options": shuffled,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "category": default_category or "AI Trivia",
            "difficulty": difficulty or "medium",
            "source": "Gemini AI"
        }

    def explain_answer(self, question: str, player_answer: str, correct_answer: str) -> str:
        """
        Optionally ask Gemini for a personalized, witty explanation.
        Falls back to default string on error.
        """
        if not self.is_available():
            return f"The correct answer is '{correct_answer}'."

        prompt = (
            f"In a trivia quiz, the question was: '{question}'.\n"
            f"The player selected: '{player_answer}'.\n"
            f"The correct answer is: '{correct_answer}'.\n"
            f"Provide a friendly, educational 1-2 sentence explanation clarifying why "
            f"'{correct_answer}' is correct."
        )

        try:
            response = self.client.models.generate_content(
                model=CANDIDATE_MODELS[0],
                contents=prompt
            )
            return response.text.strip()
        except Exception:
            return f"'{correct_answer}' is the correct answer."


# Module-level singleton
_gemini_client = GeminiClient()


def get_gemini_question(category: str = "General Knowledge", difficulty: str = "medium") -> dict:
    """Helper function to fetch a single AI-generated question."""
    return _gemini_client.generate_question(category=category, difficulty=difficulty)


def check_gemini_status() -> bool:
    """Check if Gemini API key is configured."""
    return _gemini_client.is_available()
