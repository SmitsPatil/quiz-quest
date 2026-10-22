"""
Quiz Quest - High Scores & Leaderboard Module
Handles persistence and sorting of player rankings in data/leaderboard.json.
"""

import json
import os
from datetime import datetime

LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "data", "leaderboard.json")


def load_leaderboard():
    """Load leaderboard entries from JSON file, returning sorted list."""
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                # Sort descending by score, then level
                return sorted(data, key=lambda x: (x.get("score", 0), x.get("level", 1)), reverse=True)
    except Exception as e:
        print(f"[Leaderboard] Error loading file: {e}")
    return []


def save_leaderboard_entry(name: str, score: int, level: int, mode: str = "Mixed Mode"):
    """
    Save a new player score to the leaderboard.
    Keeps the list sorted and capped at top 20 entries.
    """
    clean_name = (name or "Anonymous").strip()[:16]
    if not clean_name:
        clean_name = "Player"

    today_str = datetime.now().strftime("%Y-%m-%d")
    new_entry = {
        "name": clean_name,
        "score": int(score),
        "level": int(level),
        "mode": mode,
        "date": today_str
    }

    entries = load_leaderboard()
    entries.append(new_entry)
    entries.sort(key=lambda x: (x.get("score", 0), x.get("level", 1)), reverse=True)
    # Keep top 20 for storage
    entries = entries[:20]

    os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        return True
    except Exception as e:
        print(f"[Leaderboard] Error saving entry: {e}")
        return False


def get_top_entries(limit: int = 10):
    """Retrieve top N leaderboard entries."""
    entries = load_leaderboard()
    return entries[:limit]


def is_eligible_for_leaderboard(score: int, limit: int = 10) -> bool:
    """Check if the given score qualifies for the top N leaderboard."""
    if score <= 0:
        return False
    entries = load_leaderboard()
    if len(entries) < limit:
        return True
    return score > entries[limit - 1].get("score", 0)
