"""
Quiz Quest – AI-Powered Quiz Adventure Website
Flask Backend Server
Coordinates OpenTDB API, Google Gemini API, Local Storage Fallbacks,
and Leaderboard endpoints with server-side validation.
"""

import json
import os
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()

from services.opentdb import opentdb_service, OPENTDB_CATEGORIES
from services.gemini import gemini_service

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard.json")
TMP_LEADERBOARD_FILE = os.path.join("/tmp", "leaderboard.json")

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

# Level to difficulty mapping
LEVEL_DIFFICULTIES = {
    1: "easy",
    2: "easy",
    3: "medium",
    4: "medium",
    5: "hard"
}


def load_local_questions():
    """Load offline fallback questions from JSON file."""
    if os.path.exists(QUESTIONS_FILE):
        try:
            with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[App] Error reading questions.json: {e}")
    return []


def get_local_fallback(category: str = None, difficulty: str = "medium") -> dict:
    """Select a question from local vault with matching difficulty/category."""
    questions = load_local_questions()
    if not questions:
        # Hardcoded emergency fallback
        return {
            "question": "What is the speed of light in a vacuum (approximate)?",
            "options": ["300,000 km/s", "150,000 km/s", "30,000 km/s", "3,000 km/s"],
            "correct_answer": "300,000 km/s",
            "explanation": "Light travels at roughly 299,792 km/s in empty space.",
            "category": "Science",
            "difficulty": difficulty or "medium",
            "source": "Local Quest Vault"
        }

    # Match difficulty if possible
    diff_matches = [q for q in questions if q.get("difficulty") == difficulty]
    pool = diff_matches if diff_matches else questions
    selected = random.choice(pool)

    options = list(selected.get("options", []))
    random.shuffle(options)

    return {
        "question": selected.get("question"),
        "options": options,
        "correct_answer": selected.get("correct_answer"),
        "explanation": selected.get("explanation", f"'{selected.get('correct_answer')}' is the verified answer."),
        "category": selected.get("category", "General"),
        "difficulty": selected.get("difficulty", difficulty),
        "source": "Local Quest Vault"
    }


def load_leaderboard_data():
    """Load leaderboard rankings, checking /tmp first if on serverless."""
    for target in [TMP_LEADERBOARD_FILE, LEADERBOARD_FILE]:
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return sorted(data, key=lambda x: (x.get("score", 0), x.get("level", 1)), reverse=True)
            except Exception as e:
                print(f"[App] Error reading {target}: {e}")
    return []


def save_leaderboard_entry(entry: dict):
    """Save valid entry to leaderboard, supporting both local filesystem and serverless /tmp."""
    entries = load_leaderboard_data()
    entries.append(entry)
    entries.sort(key=lambda x: (x.get("score", 0), x.get("level", 1)), reverse=True)
    entries = entries[:20]

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        return True
    except (OSError, PermissionError):
        # Serverless environment: write to /tmp
        try:
            with open(TMP_LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
            return True
        except Exception as e:
            print(f"[App] Serverless /tmp write error: {e}")
            return True
    except Exception as e:
        print(f"[App] Error saving leaderboard: {e}")
        return False


# -------------------------------------------------------------
# Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    """Render the single-page Quiz Quest Web Application."""
    return render_template("index.html")


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Return available trivia categories."""
    categories = list(OPENTDB_CATEGORIES.keys())
    return jsonify({"categories": categories})


@app.route("/api/question", methods=["POST"])
def get_question():
    """
    Fetch a single question according to selected mode, category, and level.
    Guarantees 100% uptime with 3-tier fallback (Primary -> Secondary -> Local).
    """
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "mixed").lower()
    category = data.get("category", "All Categories")
    difficulty = data.get("difficulty", "Progressive")
    level = int(data.get("level", 1))
    q_index = int(data.get("question_number", 1))

    # Resolve difficulty
    if difficulty.lower() == "progressive":
        resolved_diff = LEVEL_DIFFICULTIES.get(level, "medium")
    else:
        resolved_diff = difficulty.lower()

    question_data = None

    if mode == "classic":
        # OpenTDB -> Gemini -> Local
        question_data = opentdb_service.get_question(category, resolved_diff)
        if not question_data:
            question_data = gemini_service.generate_question(category, resolved_diff)

    elif mode == "ai":
        # Gemini -> OpenTDB -> Local
        question_data = gemini_service.generate_question(category, resolved_diff)
        if not question_data:
            question_data = opentdb_service.get_question(category, resolved_diff)

    else:  # "mixed"
        # Alternate: Odd question numbers OpenTDB, Even question numbers Gemini
        if q_index % 2 == 1:
            question_data = opentdb_service.get_question(category, resolved_diff)
            if not question_data:
                question_data = gemini_service.generate_question(category, resolved_diff)
        else:
            question_data = gemini_service.generate_question(category, resolved_diff)
            if not question_data:
                question_data = opentdb_service.get_question(category, resolved_diff)

    # Final fallback to Local Vault
    if not question_data:
        question_data = get_local_fallback(category, resolved_diff)

    return jsonify({"success": True, "question": question_data})


@app.route("/api/bonus", methods=["POST"])
def get_bonus_question():
    """Generate an AI Boss Challenge for level completion."""
    data = request.get_json(silent=True) or {}
    level = int(data.get("level", 5))

    bonus = gemini_service.generate_bonus_riddle(level=level)
    if not bonus:
        # Fallback to hard local question
        bonus = get_local_fallback(category="Science & Nature", difficulty="hard")
        bonus["category"] = "Ancient Boss Challenge"

    return jsonify({"success": True, "question": bonus})


@app.route("/api/explain", methods=["POST"])
def explain_answer():
    """Dynamic AI explanation endpoint."""
    data = request.get_json(silent=True) or {}
    q = data.get("question", "")
    p_ans = data.get("player_answer", "")
    c_ans = data.get("correct_answer", "")

    explanation = gemini_service.explain_answer(q, p_ans, c_ans)
    return jsonify({"explanation": explanation})


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    """Return top 10 rankings."""
    entries = load_leaderboard_data()
    return jsonify({"leaderboard": entries[:10]})


@app.route("/api/leaderboard", methods=["POST"])
def post_leaderboard():
    """Submit a score with server-side validation."""
    data = request.get_json(silent=True) or {}

    raw_name = data.get("name", "Adventurer")
    clean_name = str(raw_name).strip()[:18] or "Adventurer"

    try:
        score = max(0, int(data.get("score", 0)))
        accuracy = max(0, min(100, int(data.get("accuracy", 0))))
        level = max(1, min(5, int(data.get("level", 1))))
        mode = str(data.get("mode", "Mixed Mode"))[:20]
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid numerical parameters"}), 400

    entry = {
        "name": clean_name,
        "score": score,
        "accuracy": accuracy,
        "level": level,
        "mode": mode,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    success = save_leaderboard_entry(entry)
    top_10 = load_leaderboard_data()[:10]
    return jsonify({"success": success, "leaderboard": top_10})


@app.route("/api/status", methods=["GET"])
def get_status():
    """Return live API health checks."""
    local_count = len(load_local_questions())
    return jsonify({
        "opentdb": opentdb_service.check_health(),
        "gemini": gemini_service.is_available(),
        "local": local_count > 0,
        "local_questions_count": local_count
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================")
    print(f"  Quiz Quest – AI-Powered Quiz Adventure Website")
    print(f"  Running locally at http://localhost:{port}")
    print(f"==================================================\n")
    app.run(host="127.0.0.1", port=port, debug=True)
