# ⚔️ Quiz Quest – AI-Powered Quiz Adventure Website

An interactive, responsive quiz adventure web application combining the **Open Trivia Database (OpenTDB) REST API** and the **Google Gemini API** with a **Python Flask backend** and modern **Vanilla HTML5/CSS3/JavaScript frontend**.

---

## 🌟 Overview & Key Highlights

**Quiz Quest** is an educational, full-stack quiz adventure game. It demonstrates how to combine **public REST APIs (OpenTDB)** with **Generative AI (Google Gemini)** in a cohesive, responsive web gaming application.

- **Dual-API Engine:** Fetches standard trivia from OpenTDB and generates dynamic trivia questions and explanations with Google Gemini.
- **Three Playable Modes:**
  1. **Classic Mode:** Trivia from the Open Trivia Database.
  2. **AI Mode:** Dynamically generated questions and explanations powered by Google Gemini.
  3. **Mixed Mode:** Automatically alternates between OpenTDB and Gemini.
- **Resilient 3-Tier Fallback Pipeline:**
  $$\text{Target API} \longrightarrow \text{Secondary API} \longrightarrow \text{Local Quest Vault (JSON)}$$
  If an API times out, hits rate limits, or if internet access is down, the website falls back automatically to guarantee **100% offline uptime**.
- **In-Browser Web Audio Synthesizer:** Pure procedural synthesis via the Web Audio API—retro-modern chimes, ticks, buzzes, and fanfare with **zero external audio file downloads**.
- **Interactive Particle System & Celebratory Confetti:** Ambient canvas particles and physics-based confetti bursts upon quest completion.
- **Persistent Leaderboard:** Server-side JSON storage preserving top 10 scores, accuracy, player names, and completion dates.

---

## 🏗️ Architecture & Project Structure

```text
QuizQuest/
├── app.py                   # Flask server coordinating routes, fallback, and validation
├── requirements.txt         # Python dependencies (Flask, google-genai, requests, etc.)
├── .env.example             # Template for API credentials
├── .env                     # Active environment configuration (API Key)
├── .gitignore               # Git rules protecting secrets and caches
├── services/
│   ├── opentdb.py           # OpenTDB REST API client with batch caching & HTML unescaping
│   └── gemini.py            # Gemini client with structured JSON parsing & validation
├── data/
│   ├── questions.json       # Curated offline question vault (25+ questions)
│   └── leaderboard.json     # Persistent Hall of Fame high scores
├── templates/
│   └── index.html           # Responsive single-page HTML5 web application
├── static/
│   ├── css/
│   │   └── style.css        # Rich responsive CSS design system (glassmorphism & animations)
│   └── js/
│       └── game.js          # Client controller, Web Audio engine, timer & confetti
├── test_web_app.py          # Automated Flask API test suite (8 tests)
├── test_quiz_quest.py       # Automated desktop engine test suite (7 tests)
└── README.md                # Project documentation & college viva guide
```

---

## 🎮 Web Pages & Features

### A. Home Page
- **Logo & Emblem:** Pulsing orbital emblem with glowing brand title.
- **Live Status Ribbon:** Real-time health pills indicating the connectivity of **Gemini AI**, **Open Trivia DB**, and the **Offline Vault**.
- **Navigation:** Quick access to Begin Quest, How to Play guide modal, and Hall of Fame.

### B. Game Setup
- **Player Name:** Stored in browser `localStorage`.
- **Mode Selector:** Choose between **Mixed Mode** (Alternating), **Classic Mode** (OpenTDB), or **AI Mode** (Gemini).
- **Realm Category:** 12 categories including General Knowledge, Science & Nature, Computers & Tech, History, Geography, Entertainment, Mythology, Sports, etc.
- **Difficulty:** Progressive (adapts level by level from Easy to Hard) or fixed.
- **Quest Length:** Choose campaign length (15 questions across 5 levels, 10 questions, or 5-question blitz).

### C. Quiz Gameplay
- **Single Question Focus:** Clean, distraction-free cards with 4 multiple-choice options (`A, B, C, D`).
- **Source Badges:** Clearly labels questions with glowing tags:
  - 🤖 `Gemini AI` (Purple glow)
  - 🌐 `Open Trivia DB` (Blue glow)
  - 💾 `Local Quest Vault` (Teal glow)
- **HUD (Heads-Up Display):**
  - **Level Progress:** Realm indicator (Level 1 to 5) with smooth progress bar.
  - **Score Counter:** Live gold score display (+10 points per correct answer).
  - **Hearts:** 3 lives with animated pulse and grayscale loss states.
  - **Circular SVG Countdown Timer:** 20-second countdown with smooth circular SVG stroke animation that turns amber and red under 5 seconds.
- **Immediate Feedback:**
  - Highlights correct option in luminous emerald green (`#10b981`).
  - Highlights wrong choice in crimson red (`#ef4444`).
  - Plays procedural Web Audio chimes or buzzes.
- **Knowledge Insight Card:** Reveals the educational explanation for why the answer is true.
- **Level Transitions:** Modal celebrations when advancing across the 5 realm tiers.
- **Results Screen:** Detailed performance breakdown with accuracy percentage, realm reached, survival bonus (+20 pts per remaining heart), and confetti burst.

### D. Hall of Fame Leaderboard
- Top 10 rankings table with rank medals (🥇 1st, 🥈 2nd, 🥉 3rd), player name, score, accuracy percentage, realm level, mode, and date.
- Server-side validation on `/api/leaderboard` to prevent corrupted entries.

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. API Key Configuration
The Gemini API key is loaded via `python-dotenv` from the `.env` file or from your system environment variables. **No API keys are exposed in frontend JavaScript or hardcoded in python source code.**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set your Google Gemini API key:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```
*(Free Gemini API keys can be generated at [Google AI Studio](https://aistudio.google.com/)).*

---

## 🚀 Running the Web Application

Start the Flask development server:

```bash
python app.py
```

Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 🧪 Automated Testing & Verification

Run the automated test suite verifying all routes, APIs, fallback mechanisms, and leaderboard endpoints:

```bash
python test_web_app.py
```

### Test Suite Output:
```text
........
----------------------------------------------------------------------
Ran 8 tests in 9.901s

OK

[Web Test 1] Testing Homepage rendering...
  [PASS] Homepage rendered successfully (HTTP 200).

[Web Test 2] Testing /api/categories endpoint...
  [PASS] Categories retrieved: 12 available.

[Web Test 3] Testing /api/question in Classic Mode (OpenTDB)...
  [PASS] Classic question: 'What do sailors call the back of a boat?...' (Source: Open Trivia DB)

[Web Test 4] Testing /api/question in AI Mode (Gemini)...
  [PASS] AI question: 'What is the primary gas found in the atmosphere of...' (Source: Gemini AI)

[Web Test 5] Testing /api/question in Mixed Mode alternation...
  [PASS] Turn 1 Source: Open Trivia DB
  [PASS] Turn 2 Source: Gemini AI

[Web Test 6] Testing offline fallback resilience...
  [PASS] Successfully fell back to Local Quest Vault: 'Which programming language was created by Gui...'

[Web Test 7] Testing Leaderboard submission and top 10 retrieval...
  [PASS] Top leaderboard entry: TestKnight with 999 points.

[Web Test 8] Testing /api/status health check...
  [PASS] System Health: Gemini=True, OpenTDB=True, Local=True
```

---

## 🎓 College Viva / Presentation Q&A

### Q1: Why combine OpenTDB with Google Gemini instead of using just one?
**Answer:** OpenTDB provides an instant, rate-limit-friendly database of verified human trivia, while Gemini provides infinite generative flexibility, dynamic category creation, and in-depth educational explanations. Combining both in **Mixed Mode** offers the best of both worlds: diverse questions with explanatory reasoning.

### Q2: How does the system handle internet failure or API outages?
**Answer:** Through a **3-Tier Fallback Pipeline** implemented in `app.py`:
1. The server attempts the primary API for the selected mode.
2. If that fails or times out, it attempts the secondary API.
3. If both APIs fail (e.g., offline computer or rate limit), it automatically loads from `data/questions.json`. The web app never crashes or displays a blank screen.

### Q3: How is the Gemini API key kept secure?
**Answer:** The API key is stored exclusively on the backend in the `.env` file and accessed via Python's `os.environ`. The client-side JavaScript only communicates with our own backend endpoints (`/api/question`, `/api/explain`), so the key is never exposed in client network inspection or page source.

### Q4: How is audio handled without external files?
**Answer:** The frontend uses the browser's native **Web Audio API** (`AudioContext`, `OscillatorNode`, and `GainNode`) to synthesize sound waves mathematically in real-time, eliminating external audio files, missing asset 404s, and extra network overhead.
