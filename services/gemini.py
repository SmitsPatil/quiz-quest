"""
Quiz Quest - Google Gemini AI Service
Generates dynamic trivia questions, structured JSON responses, answer explanations,
and bonus boss-level challenges.
"""

import json
import os
import random
from dotenv import load_dotenv

load_dotenv()

# Candidate models list with fallback
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3-flash-preview"
]


class GeminiService:
    """Service to generate trivia content using Google Gemini API."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self._init_client()
        self.batch_cache = []

    def _init_client(self):
        """Initialize Google GenAI client."""
        if not self.api_key:
            return
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"[Gemini Service] Client init error: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Gemini API key and client are ready."""
        return bool(self.api_key and self.client)

    def generate_question(self, category: str = "General Knowledge", difficulty: str = "medium") -> dict:
        """Retrieve a single question from prefetch cache or generate a fresh batch."""
        if self.batch_cache:
            return self.batch_cache.pop(0)

        batch = self.generate_batch(amount=3, category=category, difficulty=difficulty)
        if batch:
            self.batch_cache.extend(batch)
            return self.batch_cache.pop(0)

        return None

    def generate_batch(self, amount: int = 3, category: str = "General Knowledge", difficulty: str = "medium") -> list:
        """Generate structured trivia questions via Gemini in valid JSON."""
        if not self.is_available():
            self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
            self._init_client()
            if not self.is_available():
                return []

        from google.genai import types

        cat_str = category if category and category != "All Categories" else "General Knowledge, Science, or Pop Culture"
        diff_str = difficulty if difficulty else "medium"

        prompt = (
            f"You are the Quiz Master for Quiz Quest, an adventure trivia game.\n"
            f"Generate exactly {amount} engaging multiple-choice trivia questions.\n"
            f"Category focus: {cat_str}.\n"
            f"Difficulty level: {diff_str} (easy = accessible, medium = interesting, hard = challenging trivia).\n\n"
            f"Strict JSON Output Requirements:\n"
            f"Return ONLY a JSON array of objects. Each object must contain:\n"
            f"- question: (string) clear, concise trivia question\n"
            f"- options: (array of exactly 4 unique strings) one correct answer and three plausible distractors\n"
            f"- correct_answer: (string) exactly matching one of the 4 options\n"
            f"- explanation: (string) 1-2 sentence educational explanation of why the correct answer is true"
        )

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

                parsed = self._parse_and_validate(response.text.strip(), category, diff_str)
                if parsed:
                    return parsed
            except Exception as e:
                print(f"[Gemini Service] Model '{model_name}' failed: {e}")

        return []

    def _parse_and_validate(self, raw_json_str: str, default_category: str, difficulty: str) -> list:
        """Parse and strictly validate Gemini structured output."""
        try:
            data = json.loads(raw_json_str)
            if isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        data = val
                        break
                else:
                    data = [data]

            valid = []
            for item in data:
                q = self._validate_question(item, default_category, difficulty)
                if q:
                    valid.append(q)
            return valid
        except Exception as e:
            print(f"[Gemini Service] Validation error: {e}")
            return []

    def _validate_question(self, item: dict, default_category: str, difficulty: str) -> dict:
        """Validate question dictionary schema."""
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

        cleaned_options = [str(opt).strip() for opt in options]
        if len(set(cleaned_options)) != 4:
            return None

        if correct_answer not in cleaned_options:
            matches = [opt for opt in cleaned_options if opt.lower() == correct_answer.lower()]
            if matches:
                correct_answer = matches[0]
            else:
                return None

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

    def generate_bonus_riddle(self, level: int = 5) -> dict:
        """Generate an epic boss bonus question for level clear."""
        if not self.is_available():
            return None

        from google.genai import types

        prompt = (
            f"You are the Ancient Sphinx guarding Level {level} of Quiz Quest.\n"
            f"Create 1 epic, clever bonus riddle or high-stakes trivia question.\n"
            f"Return ONLY valid JSON with keys: question, options (4 strings), correct_answer, explanation."
        )

        try:
            response = self.client.models.generate_content(
                model=CANDIDATE_MODELS[0],
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.8,
                    max_output_tokens=600,
                    http_options=types.HttpOptions(timeout=15000)
                )
            )
            parsed = self._parse_and_validate(response.text.strip(), "Ancient Boss Challenge", "hard")
            if parsed:
                return parsed[0]
        except Exception as e:
            print(f"[Gemini Service] Bonus riddle error: {e}")

        return None

    def explain_answer(self, question: str, player_answer: str, correct_answer: str) -> str:
        """Provide detailed answer explanation."""
        if not self.is_available():
            return f"The correct answer is '{correct_answer}'."

        prompt = (
            f"Question: '{question}'\n"
            f"Player chose: '{player_answer}'\n"
            f"Correct answer: '{correct_answer}'\n"
            f"Provide a friendly, educational 2-sentence explanation of why '{correct_answer}' is correct."
        )

        try:
            response = self.client.models.generate_content(
                model=CANDIDATE_MODELS[0],
                contents=prompt
            )
            return response.text.strip()
        except Exception:
            return f"'{correct_answer}' is verified as the correct answer."


# Singleton instance
gemini_service = GeminiService()
