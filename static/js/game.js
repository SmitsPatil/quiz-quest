/**
 * QUIZ QUEST – Frontend Game Engine & State Controller
 * Features Web Audio procedural synthesizer, particle engines,
 * timer countdown, keyboard shortcuts, and REST API integration.
 */

// ---------------------------------------------------------------------
// 1. Audio Synthesizer (Web Audio API - In-memory procedural sounds)
// ---------------------------------------------------------------------
class SoundEngine {
  constructor() {
    this.ctx = null;
    this.muted = localStorage.getItem('quizquest_muted') === 'true';
    this.initContext();
  }

  initContext() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  resume() {
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  toggleMute() {
    this.muted = !this.muted;
    localStorage.setItem('quizquest_muted', this.muted);
    return this.muted;
  }

  playTone(freq, duration, type = 'sine', decay = 0.05) {
    if (this.muted) return;
    try {
      this.initContext();
      this.resume();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      gain.gain.setValueAtTime(0.18, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      // Audio autoplay policy fallback
    }
  }

  playClick() {
    this.playTone(880, 0.06, 'triangle');
  }

  playCorrect() {
    // Uplifting C major triad (C5, E5, G5)
    this.playTone(523.25, 0.1, 'sine');
    setTimeout(() => this.playTone(659.25, 0.12, 'sine'), 80);
    setTimeout(() => this.playTone(783.99, 0.25, 'sine'), 160);
  }

  playWrong() {
    // Dissonant descending buzz
    this.playTone(220, 0.14, 'sawtooth');
    setTimeout(() => this.playTone(155, 0.22, 'sawtooth'), 100);
  }

  playLevelUp() {
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, 0.18, 'triangle'), idx * 80);
    });
  }

  playVictory() {
    const melody = [523.25, 659.25, 783.99, 1046.50, 880, 1046.50];
    melody.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, 0.25, 'triangle'), idx * 120);
    });
  }
}

// ---------------------------------------------------------------------
// 2. Ambient Particles & Confetti Engines
// ---------------------------------------------------------------------
class AmbientParticles {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.init();
    this.animate();
  }

  resize() {
    this.w = this.canvas.width = window.innerWidth;
    this.h = this.canvas.height = window.innerHeight;
  }

  init() {
    this.particles = [];
    for (let i = 0; i < 45; i++) {
      this.particles.push({
        x: Math.random() * this.w,
        y: Math.random() * this.h,
        radius: Math.random() * 2 + 1,
        speed: Math.random() * 0.6 + 0.2,
        color: ['#38bdf8', '#a855f7', '#f59e0b', '#3b82f6'][Math.floor(Math.random() * 4)],
        alpha: Math.random() * 0.5 + 0.1
      });
    }
  }

  animate() {
    this.ctx.clearRect(0, 0, this.w, this.h);
    this.particles.forEach(p => {
      p.y -= p.speed;
      if (p.y < -10) {
        p.y = this.h + 10;
        p.x = Math.random() * this.w;
      }
      this.ctx.fillStyle = p.color;
      this.ctx.globalAlpha = p.alpha;
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      this.ctx.fill();
    });
    this.ctx.globalAlpha = 1;
    requestAnimationFrame(() => this.animate());
  }
}

class ConfettiEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.active = false;
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.w = this.canvas.width = window.innerWidth;
    this.h = this.canvas.height = window.innerHeight;
  }

  burst() {
    this.active = true;
    this.particles = [];
    const colors = ['#38bdf8', '#a855f7', '#f59e0b', '#10b981', '#ec4899', '#ffffff'];
    for (let i = 0; i < 120; i++) {
      this.particles.push({
        x: this.w / 2,
        y: this.h / 2,
        vx: (Math.random() - 0.5) * 18,
        vy: (Math.random() - 0.7) * 22,
        size: Math.random() * 8 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        vr: (Math.random() - 0.5) * 10,
        gravity: 0.45,
        alpha: 1
      });
    }
    this.render();
  }

  render() {
    if (!this.active) return;
    this.ctx.clearRect(0, 0, this.w, this.h);
    let alive = false;
    this.particles.forEach(p => {
      p.vy += p.gravity;
      p.x += p.vx;
      p.y += p.vy;
      p.rotation += p.vr;
      p.alpha -= 0.007;

      if (p.alpha > 0) {
        alive = true;
        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate((p.rotation * Math.PI) / 180);
        this.ctx.fillStyle = p.color;
        this.ctx.globalAlpha = Math.max(0, p.alpha);
        this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        this.ctx.restore();
      }
    });

    if (alive) {
      requestAnimationFrame(() => this.render());
    } else {
      this.active = false;
      this.ctx.clearRect(0, 0, this.w, this.h);
    }
  }
}

// ---------------------------------------------------------------------
// 3. Central Game Controller
// ---------------------------------------------------------------------
class QuizQuestApp {
  constructor() {
    this.sound = new SoundEngine();
    this.particles = new AmbientParticles('particleCanvas');
    this.confetti = new ConfettiEngine('confettiCanvas');

    // State Variables
    this.playerName = localStorage.getItem('quizquest_player_name') || 'Adventurer';
    this.mode = 'mixed';
    this.category = 'All Categories';
    this.difficulty = 'Progressive';
    this.totalQuestionsTarget = 15;
    this.questionsPerLevel = 3;

    this.score = 0;
    this.lives = 3;
    this.maxLives = 3;
    this.level = 1;
    this.maxLevels = 5;
    this.currentQIndex = 0;
    this.totalAnswered = 0;
    this.totalCorrect = 0;

    // Active Question & Timer
    this.currentQuestion = null;
    this.timerSeconds = 20;
    this.maxTimer = 20;
    this.timerInterval = null;
    this.isAnsweringLocked = false;

    this.initDOM();
    this.bindEvents();
    this.checkAPIStatus();
    this.updateSoundIcon();
  }

  initDOM() {
    // Screens
    this.screens = {
      home: document.getElementById('homeScreen'),
      setup: document.getElementById('setupScreen'),
      game: document.getElementById('gameScreen'),
      results: document.getElementById('resultsScreen'),
      leaderboard: document.getElementById('leaderboardScreen')
    };

    // Modals
    this.levelModal = document.getElementById('levelModal');
    this.helpModal = document.getElementById('howToPlayModal');

    // HUD Elements
    this.hudLevelText = document.getElementById('hudLevelText');
    this.hudProgressFill = document.getElementById('hudProgressFill');
    this.hudQuestionCount = document.getElementById('hudQuestionCount');
    this.hudScoreText = document.getElementById('hudScoreText');
    this.hudHearts = document.getElementById('hudHearts');
    this.timerText = document.getElementById('timerSecondsText');
    this.timerCircleProgress = document.getElementById('timerCircleProgress');

    // Question Elements
    this.sourceBadge = document.getElementById('questionSourceBadge');
    this.categoryTag = document.getElementById('questionCategoryTag');
    this.questionText = document.getElementById('questionText');
    this.optionsGrid = document.getElementById('optionsGrid');
    this.feedbackCard = document.getElementById('feedbackCard');
    this.feedbackStatus = document.getElementById('feedbackStatus');
    this.feedbackIcon = document.getElementById('feedbackIcon');
    this.feedbackTitle = document.getElementById('feedbackTitle');
    this.explanationText = document.getElementById('explanationText');

    // Form Inputs
    document.getElementById('playerNameInput').value = this.playerName;
  }

  showScreen(name) {
    Object.values(this.screens).forEach(screen => screen.classList.remove('active'));
    if (this.screens[name]) {
      this.screens[name].classList.add('active');
    }
  }

  bindEvents() {
    // Sound Toggle
    document.getElementById('soundToggleBtn').addEventListener('click', () => {
      const isMuted = this.sound.toggleMute();
      this.updateSoundIcon();
    });

    // Navigation Buttons
    document.getElementById('brandLogo').addEventListener('click', () => {
      this.sound.playClick();
      this.showScreen('home');
    });

    document.getElementById('startSetupBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.showScreen('setup');
    });

    document.getElementById('howToPlayBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.helpModal.classList.remove('hidden');
    });

    document.getElementById('closeHelpModalBtn').addEventListener('click', () => {
      this.helpModal.classList.add('hidden');
    });

    document.getElementById('understoodHelpBtn').addEventListener('click', () => {
      this.helpModal.classList.add('hidden');
    });

    document.getElementById('navLeaderboardBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.loadLeaderboard();
      this.showScreen('leaderboard');
    });

    document.getElementById('backFromLeaderboardBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.showScreen('home');
    });

    document.getElementById('cancelSetupBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.showScreen('home');
    });

    // Setup Form Interactions
    this.setupSegmentedControls();

    // Start Game
    document.getElementById('setupForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.sound.playClick();
      this.startNewGame();
    });

    // Question Continuation
    document.getElementById('continueQuestionBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.advanceAfterFeedback();
    });

    // Level Up Modal Proceed
    document.getElementById('proceedNextLevelBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.levelModal.classList.add('hidden');
      this.fetchNextQuestion();
    });

    // Results Actions
    document.getElementById('playAgainBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.showScreen('setup');
    });

    document.getElementById('resultsViewLeaderboardBtn').addEventListener('click', () => {
      this.sound.playClick();
      this.loadLeaderboard();
      this.showScreen('leaderboard');
    });

    // Keyboard Shortcuts (1-4, A-D, Space, M)
    window.addEventListener('keydown', (e) => {
      if (e.key === 'm' || e.key === 'M') {
        this.sound.toggleMute();
        this.updateSoundIcon();
        return;
      }

      if (this.screens.game.classList.contains('active')) {
        if (!this.isAnsweringLocked) {
          const keyMap = { '1': 0, 'a': 0, 'A': 0, '2': 1, 'b': 1, 'B': 1, '3': 2, 'c': 2, 'C': 2, '4': 3, 'd': 3, 'D': 3 };
          if (e.key in keyMap) {
            this.handleOptionSelect(keyMap[e.key]);
          }
        } else if (!this.feedbackCard.classList.contains('hidden')) {
          if (e.key === ' ' || e.key === 'Enter') {
            this.advanceAfterFeedback();
          }
        }
      }
    });
  }

  setupSegmentedControls() {
    // Mode Buttons
    document.querySelectorAll('#modeSelector .segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.sound.playClick();
        document.querySelectorAll('#modeSelector .segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.mode = btn.dataset.mode;
      });
    });

    // Difficulty Buttons
    document.querySelectorAll('#difficultySelector .pill-option').forEach(btn => {
      btn.addEventListener('click', () => {
        this.sound.playClick();
        document.querySelectorAll('#difficultySelector .pill-option').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.difficulty = btn.dataset.diff;
      });
    });

    // Length Buttons
    document.querySelectorAll('#lengthSelector .pill-option').forEach(btn => {
      btn.addEventListener('click', () => {
        this.sound.playClick();
        document.querySelectorAll('#lengthSelector .pill-option').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.totalQuestionsTarget = parseInt(btn.dataset.length, 10);
        this.questionsPerLevel = Math.max(1, Math.round(this.totalQuestionsTarget / this.maxLevels));
      });
    });
  }

  updateSoundIcon() {
    document.getElementById('soundIcon').textContent = this.sound.muted ? '🔇' : '🔊';
  }

  async checkAPIStatus() {
    try {
      const resp = await fetch('/api/status');
      const data = await resp.json();

      const pillGemini = document.getElementById('pillGemini');
      const pillOpentdb = document.getElementById('pillOpentdb');
      const pillLocal = document.getElementById('pillLocal');

      if (data.gemini) {
        pillGemini.classList.add('online');
        pillGemini.querySelector('.state-text').textContent = 'Online';
      } else {
        pillGemini.classList.add('offline');
        pillGemini.querySelector('.state-text').textContent = 'Key Missing';
      }

      if (data.opentdb) {
        pillOpentdb.classList.add('online');
        pillOpentdb.querySelector('.state-text').textContent = 'Online';
      } else {
        pillOpentdb.classList.add('offline');
        pillOpentdb.querySelector('.state-text').textContent = 'Unavailable';
      }

      pillLocal.classList.add('online');
      pillLocal.querySelector('.state-text').textContent = `${data.local_questions_count || 25} Loaded`;
    } catch (e) {
      console.warn('Status check unreachable:', e);
    }
  }

  startNewGame() {
    const rawName = document.getElementById('playerNameInput').value.trim();
    this.playerName = rawName || 'Adventurer';
    localStorage.setItem('quizquest_player_name', this.playerName);

    this.category = document.getElementById('categorySelect').value;
    this.score = 0;
    this.lives = this.maxLives;
    this.level = 1;
    this.currentQIndex = 0;
    this.totalAnswered = 0;
    this.totalCorrect = 0;

    this.updateHUD();
    this.showScreen('game');
    this.fetchNextQuestion();
  }

  updateHUD() {
    this.hudLevelText.textContent = `LEVEL ${this.level} / ${this.maxLevels}`;
    this.hudScoreText.textContent = this.score;
    this.hudQuestionCount.textContent = `${this.currentQIndex + 1} / ${this.totalQuestionsTarget}`;

    // Progress bar fill (within level)
    const qInCurrentLevel = (this.currentQIndex % this.questionsPerLevel);
    const progressRatio = Math.min(100, (qInCurrentLevel / this.questionsPerLevel) * 100);
    this.hudProgressFill.style.width = `${progressRatio}%`;

    // Hearts representation
    const heartSpans = this.hudHearts.querySelectorAll('.heart');
    heartSpans.forEach((heart, idx) => {
      if (idx < this.lives) {
        heart.classList.remove('lost');
      } else {
        heart.classList.add('lost');
      }
    });
  }

  startTimer() {
    clearInterval(this.timerInterval);
    this.timerSeconds = this.maxTimer;
    this.updateTimerUI();

    this.timerInterval = setInterval(() => {
      this.timerSeconds--;
      this.updateTimerUI();

      if (this.timerSeconds <= 0) {
        clearInterval(this.timerInterval);
        this.handleTimeout();
      }
    }, 1000);
  }

  updateTimerUI() {
    this.timerText.textContent = this.timerSeconds;
    const progressPercent = (this.timerSeconds / this.maxTimer) * 100;
    this.timerCircleProgress.setAttribute('stroke-dasharray', `${progressPercent}, 100`);

    if (this.timerSeconds <= 5) {
      this.timerCircleProgress.className.baseVal = 'circle danger';
    } else if (this.timerSeconds <= 10) {
      this.timerCircleProgress.className.baseVal = 'circle warning';
    } else {
      this.timerCircleProgress.className.baseVal = 'circle';
    }
  }

  stopTimer() {
    clearInterval(this.timerInterval);
  }

  async fetchNextQuestion() {
    this.isAnsweringLocked = true;
    this.feedbackCard.classList.add('hidden');
    this.questionText.textContent = 'Consulting the Oracle for your question...';

    // Clear option texts and styles
    const optionBtns = this.optionsGrid.querySelectorAll('.option-card');
    optionBtns.forEach(btn => {
      btn.className = 'option-card glass';
      btn.disabled = true;
      btn.querySelector('.opt-text').textContent = '...';
    });

    try {
      const payload = {
        mode: this.mode,
        category: this.category,
        difficulty: this.difficulty,
        level: this.level,
        question_number: this.currentQIndex + 1
      };

      const resp = await fetch('/api/question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (data.success && data.question) {
        this.renderQuestion(data.question);
      } else {
        throw new Error('Malformed question payload');
      }
    } catch (e) {
      console.error('Fetch error:', e);
      // Emergency client fallback
      this.renderQuestion({
        question: 'Which planet is known as the Red Planet?',
        options: ['Mars', 'Venus', 'Jupiter', 'Mercury'],
        correct_answer: 'Mars',
        explanation: 'Mars appears reddish due to iron oxide rust on its surface.',
        source: 'Local Quest Vault',
        category: 'Science & Nature',
        difficulty: 'easy'
      });
    }
  }

  renderQuestion(q) {
    this.currentQuestion = q;
    this.questionText.textContent = q.question;

    // Source Badge Configuration
    const src = q.source || 'Trivia';
    this.sourceBadge.className = 'source-badge';
    let icon = '💾';
    if (src.includes('Gemini')) {
      this.sourceBadge.classList.add('badge-gemini');
      icon = '🤖';
    } else if (src.includes('Open')) {
      this.sourceBadge.classList.add('badge-opentdb');
      icon = '🌐';
    } else {
      this.sourceBadge.classList.add('badge-local');
      icon = '💾';
    }
    this.sourceBadge.querySelector('.badge-icon').textContent = icon;
    this.sourceBadge.querySelector('.badge-name').textContent = src;

    // Meta Tag
    this.categoryTag.textContent = `${q.category || 'General'} • ${(q.difficulty || 'medium').toUpperCase()}`;

    // Render Options
    const optionBtns = this.optionsGrid.querySelectorAll('.option-card');
    q.options.forEach((optText, idx) => {
      if (optionBtns[idx]) {
        optionBtns[idx].querySelector('.opt-text').textContent = optText;
        optionBtns[idx].disabled = false;
        optionBtns[idx].onclick = () => this.handleOptionSelect(idx);
      }
    });

    this.isAnsweringLocked = false;
    this.updateHUD();
    this.startTimer();
  }

  handleOptionSelect(chosenIdx) {
    if (this.isAnsweringLocked) return;
    this.isAnsweringLocked = true;
    this.stopTimer();

    const chosenText = this.currentQuestion.options[chosenIdx];
    const correctText = this.currentQuestion.correct_answer;
    const isCorrect = (chosenText.trim().toLowerCase() === correctText.trim().toLowerCase());

    this.totalAnswered++;
    const optionBtns = this.optionsGrid.querySelectorAll('.option-card');

    if (isCorrect) {
      this.totalCorrect++;
      this.score += 10;
      this.sound.playCorrect();

      optionBtns[chosenIdx].classList.add('correct');
      this.showFeedback(true, 'CORRECT! Outstanding knowledge (+10 Pts)');
    } else {
      this.lives--;
      this.sound.playWrong();

      optionBtns[chosenIdx].classList.add('wrong');
      // Highlight the correct option
      optionBtns.forEach(btn => {
        if (btn.querySelector('.opt-text').textContent.trim().toLowerCase() === correctText.trim().toLowerCase()) {
          btn.classList.add('correct');
        }
      });
      this.showFeedback(false, 'INCORRECT! One life lost.');
    }

    this.updateHUD();
  }

  handleTimeout() {
    if (this.isAnsweringLocked) return;
    this.isAnsweringLocked = true;
    this.sound.playWrong();

    this.lives--;
    this.totalAnswered++;

    const correctText = this.currentQuestion.correct_answer;
    const optionBtns = this.optionsGrid.querySelectorAll('.option-card');
    optionBtns.forEach(btn => {
      if (btn.querySelector('.opt-text').textContent.trim().toLowerCase() === correctText.trim().toLowerCase()) {
        btn.classList.add('correct');
      }
    });

    this.showFeedback(false, 'TIME EXPIRED! One life lost.');
    this.updateHUD();
  }

  showFeedback(isCorrect, title) {
    this.feedbackStatus.className = `feedback-status ${isCorrect ? 'correct' : 'wrong'}`;
    this.feedbackIcon.textContent = isCorrect ? '✔' : '✖';
    this.feedbackTitle.textContent = title;
    this.explanationText.textContent = this.currentQuestion.explanation || 'Verified by the trivia engine.';

    this.feedbackCard.classList.remove('hidden');
  }

  advanceAfterFeedback() {
    this.feedbackCard.classList.add('hidden');

    if (this.lives <= 0) {
      this.endGame(false);
      return;
    }

    this.currentQIndex++;

    // Check if entire campaign finished
    if (this.currentQIndex >= this.totalQuestionsTarget) {
      this.endGame(true);
      return;
    }

    // Check for Level Clear Transition
    if (this.currentQIndex % this.questionsPerLevel === 0) {
      if (this.level < this.maxLevels) {
        this.level++;
        this.showLevelTransition();
        return;
      }
    }

    this.fetchNextQuestion();
  }

  showLevelTransition() {
    this.sound.playLevelUp();
    document.getElementById('levelModalTitle').textContent = `LEVEL ${this.level - 1} MASTERED!`;
    document.getElementById('levelModalDesc').textContent =
      `You have passed the trials of Level ${this.level - 1}. Entering Realm Tier ${this.level}...`;
    document.getElementById('levelStatsScore').textContent = this.score;
    document.getElementById('levelStatsHearts').textContent = '❤️'.repeat(this.lives);

    this.levelModal.classList.remove('hidden');
  }

  endGame(isVictory) {
    this.stopTimer();

    if (isVictory) {
      // Survival Bonus (+20 points per remaining life)
      const bonus = this.lives * 20;
      this.score += bonus;
      this.sound.playVictory();
      this.confetti.burst();

      document.getElementById('resultsEmblem').textContent = '🏆';
      document.getElementById('resultsTitle').textContent = 'QUEST CONQUERED!';
      document.getElementById('resultsSubtitle').textContent = 'All Realms Cleared – Hail the Grand Scholar!';
      document.getElementById('resultSurvivalBonus').textContent = `+${bonus}`;
    } else {
      this.sound.playTone(180, 0.4, 'sawtooth');
      document.getElementById('resultsEmblem').textContent = '💀';
      document.getElementById('resultsTitle').textContent = 'QUEST FAILED';
      document.getElementById('resultsSubtitle').textContent = `Fallen at Level ${this.level}. Rise and try again!`;
      document.getElementById('resultSurvivalBonus').textContent = '+0';
    }

    const accuracy = this.totalAnswered > 0 ? Math.round((this.totalCorrect / this.totalAnswered) * 100) : 0;
    document.getElementById('resultFinalScore').textContent = this.score;
    document.getElementById('resultAccuracy').textContent = `${accuracy}%`;
    document.getElementById('resultLevelReached').textContent = `Level ${this.level}`;
    document.getElementById('savedPlayerName').textContent = this.playerName;

    // Submit to backend leaderboard
    this.submitScore(accuracy);
    this.showScreen('results');
  }

  async submitScore(accuracy) {
    const payload = {
      name: this.playerName,
      score: this.score,
      accuracy: accuracy,
      level: this.level,
      mode: this.mode.toUpperCase() + ' Mode',
      date: new Date().toISOString().split('T')[0]
    };

    // Save to browser localStorage to guarantee persistence on player device across serverless restarts
    try {
      let localScores = JSON.parse(localStorage.getItem('quizquest_personal_scores') || '[]');
      localScores.push(payload);
      localScores.sort((a, b) => b.score - a.score);
      localScores = localScores.slice(0, 10);
      localStorage.setItem('quizquest_personal_scores', JSON.stringify(localScores));
    } catch (e) {
      console.warn('LocalStorage save error:', e);
    }

    try {
      await fetch('/api/leaderboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      console.warn('Leaderboard submission error:', e);
    }
  }

  async loadLeaderboard() {
    const tbody = document.getElementById('leaderboardTbody');
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Loading rankings...</td></tr>';

    let entries = [];
    try {
      const resp = await fetch('/api/leaderboard');
      const data = await resp.json();
      if (data.leaderboard && Array.isArray(data.leaderboard)) {
        entries = data.leaderboard;
      }
    } catch (e) {
      console.warn('Server leaderboard offline or serverless cold start:', e);
    }

    // Merge with browser localStorage personal rankings
    try {
      const localScores = JSON.parse(localStorage.getItem('quizquest_personal_scores') || '[]');
      localScores.forEach(localEntry => {
        if (!entries.some(e => e.name === localEntry.name && e.score === localEntry.score)) {
          entries.push(localEntry);
        }
      });
      entries.sort((a, b) => (b.score || 0) - (a.score || 0));
      entries = entries.slice(0, 10);
    } catch (e) {}

    if (entries.length > 0) {
      tbody.innerHTML = '';
      const medals = ['🥇 1st', '🥈 2nd', '🥉 3rd'];

      entries.forEach((entry, idx) => {
        const tr = document.createElement('tr');
        const rankLabel = idx < 3 ? medals[idx] : `#${idx + 1}`;
        tr.innerHTML = `
          <td><strong>${rankLabel}</strong></td>
          <td><strong>${this.escapeHTML(entry.name || 'Anonymous')}</strong></td>
          <td class="gold-text"><strong>${entry.score || 0}</strong></td>
          <td>${entry.accuracy || 100}%</td>
          <td>Lvl ${entry.level || 1}</td>
          <td><small>${this.escapeHTML(entry.mode || 'Mixed')}</small></td>
          <td><small>${entry.date || ''}</small></td>
        `;
        tbody.appendChild(tr);
      });
    } else {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No champions recorded yet.</td></tr>';
    }
  }

  escapeHTML(str) {
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));
  }
}

// ---------------------------------------------------------------------
// 4. Initialize Application
// ---------------------------------------------------------------------
window.addEventListener('DOMContentLoaded', () => {
  window.quizApp = new QuizQuestApp();
});
