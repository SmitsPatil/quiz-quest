# ⚔️ Quiz Quest – AI-Powered Quiz Adventure

[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?style=for-the-badge&logo=vercel)](https://vercel.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com)
[![Google Gemini API](https://img.shields.io/badge/AI-Google%20Gemini-8E75C7?style=for-the-badge&logo=google)](https://aistudio.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

An interactive, responsive trivia adventure game combining the **Open Trivia Database (OpenTDB) REST API** and the **Google Gemini Generative AI API**. Available as both a **live Vercel web application** and an **offline Pygame desktop game**.

🔗 **GitHub Repository:** [https://github.com/SmitsPatil/quiz-quest](https://github.com/SmitsPatil/quiz-quest)

---

## 🌟 Key Highlights & Innovations

- **Dual-API Intelligence:** Combines structured trivia retrieval (OpenTDB) with real-time generative reasoning and educational explanations (Google Gemini AI).
- **Three Playable Modes:**
  1. **Classic Mode:** Curated trivia questions from Open Trivia Database.
  2. **AI Mode:** Dynamically generated questions and explanations powered by Google Gemini.
  3. **Mixed Mode:** Automatically alternates between OpenTDB and Gemini questions.
- **Resilient 3-Tier Fallback Pipeline:**
  $$\text{Selected API} \longrightarrow \text{Secondary API} \longrightarrow \text{Local Quest Vault (JSON)}$$
  If an API hits rate limits, network timeouts, or if internet access is lost, the application automatically engages local fallbacks to guarantee **100% uninterrupted gameplay**.
- **Procedural Audio (Zero External Asset Overhead):**
  - **Web App:** Pure real-time synthesis via the browser's native **Web Audio API** (`AudioContext`, `OscillatorNode`, `GainNode`).
  - **Desktop App:** Pure in-memory waveform synthesis loaded into `pygame.mixer.Sound`.
- **Hall of Fame Leaderboard:** Hybrid persistence storing top 10 rankings across sessions using both server-side JSON and browser `localStorage`.
- **Enterprise Security:** API keys are never hardcoded, never exposed to client-side code, and stored exclusively in backend environment variables.

---

## 🏗️ Architecture & Project Structure

```text
QuizQuest/
├── api/
│   └── index.py             # Vercel Serverless WSGI entry point
├── app.py                   # Flask server coordinating routes, fallback, & validation
├── index.py                 # Root WSGI entry point for serverless runtimes
├── vercel.json              # Vercel deployment configuration & routing rewrites
├── requirements.txt         # Production web dependencies (Flask, google-genai, etc.)
├── requirements-desktop.txt # Optional desktop dependencies (Pygame)
├── .env.example             # Template for API credentials
├── .env                     # Local environment configuration (Git-ignored)
├── .gitignore               # Excludes secrets, cache files, and virtual environments
├── services/
│   ├── __init__.py
│   ├── opentdb.py           # OpenTDB REST client with batch caching & HTML unescaping
│   └── gemini.py            # Gemini AI client with structured JSON parsing & validation
├── data/
│   ├── questions.json       # Curated offline question vault (25+ questions)
│   └── leaderboard.json     # Persistent Hall of Fame high scores
├── templates/
│   └── index.html           # Single-page responsive HTML5 gaming interface
├── static/
│   ├── css/
│   │   └── style.css        # Rich glassmorphism CSS design system & animations
│   └── js/
│       └── game.js          # Client controller, Web Audio engine, timer & confetti
├── audio_manager.py         # Procedural sound synthesizer for Pygame desktop app
├── game.py                  # Pygame desktop game engine
├── main.py                  # Launcher for desktop Pygame edition
├── test_web_app.py          # Automated Flask API test suite (8 tests)
├── test_quiz_quest.py       # Automated desktop engine test suite (7 tests)
└── README.md                # Comprehensive documentation & college viva guide
```

---

## 🎮 Game Features & Mechanics

### 1. Main Menu & Configuration
- **Player Profile:** Hero name saved in `localStorage`.
- **Realm Selection:** 12 categories including General Knowledge, Science & Nature, Computers & Tech, History, Geography, Entertainment, Mythology, Sports, etc.
- **Difficulty:** Progressive mode (Level 1: Easy $\rightarrow$ Level 5: Hard) or fixed challenge tiers.
- **Quest Length:** Choose full campaign (15 questions across 5 levels), standard (10 questions), or quick blitz (5 questions).

### 2. Gameplay & Visual HUD
- **4 Answer Options:** Clickable cards with letter indicators (`A, B, C, D`) and keyboard shortcuts (`1-4`, `A-D`).
- **Live HUD Display:**
  - Realm level (Level 1 to 5) with smooth progress bar.
  - Question counter and live gold score (`+10 Points` per correct answer).
  - 3 Lives displayed as animated hearts (`❤️❤️❤️`) with grayscale loss states.
  - 20-second circular SVG countdown timer with dynamic color shifting.
- **Immediate Educational Feedback:** Highlights correct answer in emerald green (`#10b981`), incorrect choice in crimson red (`#ef4444`), and presents a **Knowledge Insight Card** explaining why the answer is true.
- **Level Transitions & Victory Celebrations:** Modal milestone celebrations and physics-based confetti bursts upon quest completion.

---

## ⚙️ Installation & Local Setup

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 2. Clone the Repository
```bash
git clone https://github.com/SmitsPatil/quiz-quest.git
cd quiz-quest
```

### 3. Install Dependencies
For the **Web Application**:
```bash
pip install -r requirements.txt
```

*(Optional) For the **Desktop Pygame Edition**:*
```bash
pip install -r requirements-desktop.txt
```

### 4. Configure Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your Google Gemini API key:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```
*(Get a free API key at [Google AI Studio](https://aistudio.google.com/)).*

---

## 🚀 How to Run Locally

### Option A: Web Application (Flask)
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

### Option B: Desktop Edition (Pygame)
```bash
python main.py
```

---

## ☁️ Deploying to Vercel

The application is pre-configured for **zero-friction Vercel deployment** via `vercel.json` and `api/index.py`.

### Step-by-Step Deployment:
1. Push your project to GitHub:
   ```bash
   git push -u origin main
   ```
2. Log in to [Vercel](https://vercel.com) and click **"Add New..." $\rightarrow$ "Project"**.
3. Select your `quiz-quest` GitHub repository and click **Import**.
4. In **Project Settings**:
   - **Framework Preset:** `Flask` (or `Other`)
   - **Root Directory:** `./`
5. In **Environment Variables**, add:
   - `GEMINI_API_KEY`: *Your Google Gemini API Key*
   - `GEMINI_MODEL`: `gemini-3.5-flash-lite`
6. Click **Deploy**. Vercel will build and assign a public HTTPS production URL.

---

## 🧪 Automated Testing & Verification

Run the test suites to verify backend endpoints, APIs, fallback mechanisms, and leaderboard persistence:

### 1. Web Application Test Suite
```bash
python test_web_app.py
```
```text
Ran 8 tests in 8.820s
OK

[Web Test 1] Homepage rendering: PASS (HTTP 200)
[Web Test 2] Categories endpoint: PASS (12 categories available)
[Web Test 3] Classic Mode (OpenTDB): PASS
[Web Test 4] AI Mode (Gemini AI): PASS
[Web Test 5] Mixed Mode alternation: PASS (Turn 1: OpenTDB | Turn 2: Gemini)
[Web Test 6] Offline fallback resilience: PASS (Local Quest Vault)
[Web Test 7] Leaderboard submission & retrieval: PASS
[Web Test 8] Live API health check: PASS (Gemini=True, OpenTDB=True, Local=True)
```

### 2. Desktop Pygame Engine Test Suite
```bash
python test_quiz_quest.py
```
```text
Ran 7 tests in 9.912s
OK
```

---

## 🎓 College Viva / Presentation Q&A

### Q1: Why combine OpenTDB with Google Gemini instead of using just one?
**Answer:** OpenTDB provides an instant, rate-limit-friendly database of verified human trivia, while Gemini provides infinite generative flexibility, dynamic category creation, and in-depth educational explanations. Combining both in **Mixed Mode** offers diverse questions backed by explanatory reasoning.

### Q2: How does the system handle internet failure or API outages?
**Answer:** Through a **3-Tier Fallback Pipeline** implemented in `app.py`:
1. The server attempts the primary API for the selected mode.
2. If that fails or times out, it attempts the secondary API.
3. If both APIs fail (offline computer or rate limit), it automatically loads from `data/questions.json`. The web app never crashes or displays a blank screen.

### Q3: How is the Gemini API key kept secure?
**Answer:** The API key is stored exclusively on the backend via environment variables and accessed via Python's `os.environ`. The client-side JavaScript only communicates with our backend endpoint (`/api/question`), so the key is never exposed in client network inspection or page source.

### Q4: How is audio handled without external sound files?
**Answer:** The frontend uses the browser's native **Web Audio API** (`AudioContext`, `OscillatorNode`, and `GainNode`) to synthesize sound waves mathematically in real-time, eliminating external audio files, missing asset 404s, and extra network overhead.

### Q5: How does the Leaderboard persist in a serverless environment like Vercel?
**Answer:** Serverless containers feature read-only filesystems (except `/tmp`). The application writes session data safely to `/tmp/leaderboard.json` on the server and synchronizes personal high scores with browser `localStorage`. When displaying the Hall of Fame, entries are merged dynamically so player scores persist permanently on their device.

---

## 📄 License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
