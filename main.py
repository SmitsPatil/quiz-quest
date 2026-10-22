"""
Quiz Quest – AI-Powered Adventure Game
Main Entry Point
"""

import sys
from game import QuizQuestGame


def main():
    print("=" * 60)
    print("  QUIZ QUEST: AI-Powered Adventure Game")
    print("  Powered by Pygame, OpenTDB, and Google Gemini AI")
    print("=" * 60)
    print("Initializing game engine...")
    try:
        app = QuizQuestGame()
        app.run()
    except KeyboardInterrupt:
        print("\n[QuizQuest] Game terminated by user.")
    except Exception as e:
        print(f"\n[QuizQuest] Unexpected runtime exception: {e}")
        raise
    finally:
        print("[QuizQuest] Farewell, adventurer!")
        sys.exit(0)


if __name__ == "__main__":
    main()
