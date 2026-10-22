"""
Quiz Quest - Main Pygame Engine
Features rich UI, state management, particle systems, async question loading,
interactive options, educational explanations, and leaderboard integration.
"""

import math
import os
import random
import threading
import time
import pygame
from questions import QuestionManager
from leaderboard import save_leaderboard_entry, get_top_entries, is_eligible_for_leaderboard
from audio_manager import AudioManager

# UI Dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 720
FPS = 60

# Modern Aesthetic Palette
COLOR_BG = (13, 17, 23)           # Deep Space Midnight
COLOR_BG_CARD = (22, 27, 34)      # Card surface
COLOR_BORDER = (48, 54, 61)       # Subtle border
COLOR_BORDER_HOVER = (88, 166, 255) # Electric Blue hover
COLOR_TEXT_PRIMARY = (240, 246, 252) # Crisp white
COLOR_TEXT_SECONDARY = (139, 148, 158) # Muted gray
COLOR_ACCENT_CYAN = (56, 189, 248)  # Cyan glow
COLOR_ACCENT_GOLD = (245, 158, 11)  # Amber gold for score
COLOR_CORRECT = (34, 197, 94)     # Emerald Green
COLOR_WRONG = (239, 68, 68)       # Crimson Red
COLOR_PURPLE = (168, 85, 247)     # Violet for AI badge
COLOR_BLUE = (59, 130, 246)       # Blue for OpenTDB badge
COLOR_TEAL = (20, 184, 166)       # Teal for Local Vault badge

# Game States
STATE_MENU = "menu"
STATE_CATEGORY_SELECT = "category_select"
STATE_DIFFICULTY_SELECT = "difficulty_select"
STATE_LOADING = "loading"
STATE_QUESTION = "question"
STATE_FEEDBACK = "feedback"
STATE_LEVEL_UP = "level_up"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"
STATE_LEADERBOARD = "leaderboard"
STATE_STATUS = "status"

CATEGORIES_LIST = [
    "All Categories",
    "General Knowledge",
    "Science & Nature",
    "Computers & Tech",
    "History",
    "Geography",
    "Entertainment: Film",
    "Entertainment: Music",
    "Mythology",
    "Sports"
]

DIFFICULTIES_LIST = ["Progressive", "Easy", "Medium", "Hard"]
MODES_LIST = ["Mixed Mode", "Classic Mode", "AI Mode"]


class BackgroundParticle:
    """Ambient floating particle for rich animated background."""
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.reset()
        self.y = random.uniform(0, h)

    def reset(self):
        self.x = random.uniform(0, self.w)
        self.y = self.h + random.uniform(5, 20)
        self.speed = random.uniform(0.3, 1.2)
        self.radius = random.uniform(1.0, 2.5)
        self.alpha = random.randint(40, 160)
        self.color = random.choice([
            (56, 189, 248),   # Cyan
            (168, 85, 247),  # Violet
            (59, 130, 246),  # Blue
            (245, 158, 11)   # Gold
        ])

    def update(self):
        self.y -= self.speed
        if self.y < -10:
            self.reset()

    def draw(self, surface):
        s = pygame.Surface((int(self.radius * 2 + 2), int(self.radius * 2 + 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha), (int(self.radius + 1), int(self.radius + 1)), int(self.radius))
        surface.blit(s, (self.x - self.radius, self.y - self.radius))


class FloatingText:
    """Floating score popup animation (e.g. +10 Points)."""
    def __init__(self, text, x, y, color=COLOR_ACCENT_GOLD):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.alpha = 255
        self.lifetime = 60  # frames

    def update(self):
        self.y -= 1.0
        self.alpha = max(0, self.alpha - 4)
        self.lifetime -= 1

    def draw(self, surface, font):
        if self.lifetime > 0 and self.alpha > 0:
            rendered = font.render(self.text, True, self.color)
            rendered.set_alpha(self.alpha)
            surface.blit(rendered, (self.x - rendered.get_width() // 2, self.y))


class QuizQuestGame:
    """Central Game Engine managing Pygame loop, states, rendering, and logic."""

    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Quiz Quest – AI-Powered Adventure Game")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Audio
        self.audio = AudioManager()

        # Fonts
        self.font_title = pygame.font.SysAptFont = self._get_font(42, bold=True)
        self.font_subtitle = self._get_font(20)
        self.font_heading = self._get_font(26, bold=True)
        self.font_body = self._get_font(18)
        self.font_small = self._get_font(14)
        self.font_badge = self._get_font(13, bold=True)

        # Question Manager
        self.mode_index = 0  # 0: Mixed, 1: Classic, 2: AI
        self.category_index = 0
        self.difficulty_index = 0
        self.qm = QuestionManager(mode="mixed", category="All Categories", difficulty="Progressive")

        # Game State Variables
        self.state = STATE_MENU
        self.level = 1
        self.max_levels = 5
        self.questions_per_level = 3
        self.current_q_in_level = 0
        self.total_questions_answered = 0
        self.score = 0
        self.lives = 3
        self.max_lives = 3

        # Active Question & Feedback
        self.current_question = None
        self.selected_option_idx = None
        self.is_correct = False
        self.feedback_message = ""
        self.feedback_timer = 0

        # Background particles
        self.particles = [BackgroundParticle(SCREEN_WIDTH, SCREEN_HEIGHT) for _ in range(45)]
        self.floating_texts = []

        # Async question loading
        self.is_fetching = False
        self.fetch_error = None
        self.next_fetched_question = None

        # Player Name Input for Leaderboard
        self.player_name = "Adventurer"
        self.input_active = True
        self.cursor_visible = True
        self.cursor_timer = 0
        self.score_saved = False

        # Options layout rects
        self.option_rects = []
        self.menu_buttons = {}

    def _get_font(self, size: int, bold: bool = False):
        """Find a clean modern system font or fallback to default."""
        font_names = ["Segoe UI", "Inter", "Arial", "Helvetica", "DejaVu Sans"]
        for fn in font_names:
            try:
                font = pygame.font.SysFont(fn, size, bold=bold)
                if font:
                    return font
            except Exception:
                pass
        return pygame.font.Font(None, size)

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._render()
            pygame.display.flip()

        pygame.quit()

    # ---------------------------------------------------------
    # Event Handling
    # ---------------------------------------------------------
    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.audio.toggle_mute()

                # State-specific Key Handlers
                if self.state == STATE_QUESTION and not self.is_fetching:
                    if event.key in [pygame.K_1, pygame.K_a]:
                        self._handle_option_select(0)
                    elif event.key in [pygame.K_2, pygame.K_b]:
                        self._handle_option_select(1)
                    elif event.key in [pygame.K_3, pygame.K_c]:
                        self._handle_option_select(2)
                    elif event.key in [pygame.K_4, pygame.K_d]:
                        self._handle_option_select(3)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

                elif self.state == STATE_FEEDBACK:
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                        self._advance_after_feedback()

                elif self.state == STATE_LEVEL_UP:
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                        self._start_level_question()

                elif self.state in [STATE_GAME_OVER, STATE_VICTORY]:
                    if event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        self._save_and_show_leaderboard()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU
                    elif len(self.player_name) < 14 and event.unicode.isprintable():
                        self.player_name += event.unicode

                elif self.state in [STATE_LEADERBOARD, STATE_STATUS, STATE_CATEGORY_SELECT, STATE_DIFFICULTY_SELECT]:
                    if event.key in [pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN]:
                        self.state = STATE_MENU

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(mouse_pos)

    def _handle_click(self, pos):
        """Process mouse clicks based on active state."""
        self.audio.play("click")

        # Sound toggle button (top right icon)
        mute_btn_rect = pygame.Rect(SCREEN_WIDTH - 60, 20, 40, 40)
        if mute_btn_rect.collidepoint(pos):
            self.audio.toggle_mute()
            return

        if self.state == STATE_MENU:
            for action, rect in self.menu_buttons.items():
                if rect.collidepoint(pos):
                    if action == "start":
                        self._start_new_game()
                    elif action == "mode":
                        self.mode_index = (self.mode_index + 1) % len(MODES_LIST)
                        mode_val = ["mixed", "classic", "ai"][self.mode_index]
                        self.qm.set_mode(mode_val)
                    elif action == "category":
                        self.state = STATE_CATEGORY_SELECT
                    elif action == "difficulty":
                        self.state = STATE_DIFFICULTY_SELECT
                    elif action == "leaderboard":
                        self.state = STATE_LEADERBOARD
                    elif action == "status":
                        self.state = STATE_STATUS
                    elif action == "exit":
                        self.running = False

        elif self.state == STATE_CATEGORY_SELECT:
            for idx, rect in enumerate(self.category_rects):
                if rect.collidepoint(pos):
                    self.category_index = idx
                    self.qm.set_category(CATEGORIES_LIST[idx])
                    self.state = STATE_MENU

        elif self.state == STATE_DIFFICULTY_SELECT:
            for idx, rect in enumerate(self.difficulty_rects):
                if rect.collidepoint(pos):
                    self.difficulty_index = idx
                    self.qm.set_difficulty(DIFFICULTIES_LIST[idx])
                    self.state = STATE_MENU

        elif self.state == STATE_QUESTION and not self.is_fetching:
            for idx, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    self._handle_option_select(idx)
                    break

        elif self.state == STATE_FEEDBACK:
            if hasattr(self, "continue_btn_rect") and self.continue_btn_rect.collidepoint(pos):
                self._advance_after_feedback()

        elif self.state == STATE_LEVEL_UP:
            if hasattr(self, "level_up_btn_rect") and self.level_up_btn_rect.collidepoint(pos):
                self._start_level_question()

        elif self.state in [STATE_GAME_OVER, STATE_VICTORY]:
            if hasattr(self, "submit_score_btn_rect") and self.submit_score_btn_rect.collidepoint(pos):
                self._save_and_show_leaderboard()
            elif hasattr(self, "menu_btn_rect") and self.menu_btn_rect.collidepoint(pos):
                self.state = STATE_MENU

        elif self.state in [STATE_LEADERBOARD, STATE_STATUS]:
            if hasattr(self, "back_btn_rect") and self.back_btn_rect.collidepoint(pos):
                self.state = STATE_MENU

    # ---------------------------------------------------------
    # Game Logic & Flow
    # ---------------------------------------------------------
    def _start_new_game(self):
        """Initialize parameters for a new quest run."""
        self.level = 1
        self.current_q_in_level = 0
        self.total_questions_answered = 0
        self.score = 0
        self.lives = self.max_lives
        self.score_saved = False
        self.qm.reset_session()
        self._load_next_question_async()

    def _start_level_question(self):
        """Advance into question state for current level."""
        self._load_next_question_async()

    def _load_next_question_async(self):
        """Spawn background thread to load question without freezing UI."""
        self.state = STATE_LOADING
        self.is_fetching = True
        self.fetch_error = None
        self.current_question = None

        def fetch_worker():
            try:
                q = self.qm.get_next_question(level=self.level)
                self.next_fetched_question = q
            except Exception as e:
                self.fetch_error = str(e)
            finally:
                self.is_fetching = False

        thread = threading.Thread(target=fetch_worker, daemon=True)
        thread.start()

    def _handle_option_select(self, option_index: int):
        """Process the player's answer selection."""
        if not self.current_question or option_index >= len(self.current_question["options"]):
            return

        self.selected_option_idx = option_index
        selected_text = self.current_question["options"][option_index]
        correct_text = self.current_question["correct_answer"]

        self.is_correct = (selected_text.strip().lower() == correct_text.strip().lower())
        self.current_q_in_level += 1
        self.total_questions_answered += 1

        if self.is_correct:
            self.score += 10
            self.audio.play("correct")
            self.floating_texts.append(FloatingText("+10 Points!", SCREEN_WIDTH // 2, 220, COLOR_CORRECT))
            self.feedback_message = "CORRECT! Outstanding knowledge."
        else:
            self.lives -= 1
            self.audio.play("wrong")
            self.floating_texts.append(FloatingText("-1 Life!", SCREEN_WIDTH // 2, 220, COLOR_WRONG))
            self.feedback_message = "INCORRECT! Don't lose heart."

        self.state = STATE_FEEDBACK

    def _advance_after_feedback(self):
        """Determine next state after feedback screen."""
        if self.lives <= 0:
            self.audio.play("game_over")
            self.state = STATE_GAME_OVER
            return

        # Check if current level completed
        if self.current_q_in_level >= self.questions_per_level:
            if self.level >= self.max_levels:
                # Victory! Add remaining lives bonus (+20 per life)
                bonus = self.lives * 20
                self.score += bonus
                self.audio.play("victory")
                self.state = STATE_VICTORY
            else:
                self.level += 1
                self.current_q_in_level = 0
                self.audio.play("level_up")
                self.state = STATE_LEVEL_UP
        else:
            self._load_next_question_async()

    def _save_and_show_leaderboard(self):
        """Commit high score and transition to leaderboard."""
        if not self.score_saved:
            mode_name = MODES_LIST[self.mode_index]
            save_leaderboard_entry(self.player_name, self.score, self.level, mode_name)
            self.score_saved = True
        self.state = STATE_LEADERBOARD

    # ---------------------------------------------------------
    # Updates & Animations
    # ---------------------------------------------------------
    def _update(self):
        # Update particles
        for p in self.particles:
            p.update()

        # Update floating score texts
        for ft in self.floating_texts[:]:
            ft.update()
            if ft.lifetime <= 0:
                self.floating_texts.remove(ft)

        # Handle async loading completion
        if self.state == STATE_LOADING and not self.is_fetching:
            if self.next_fetched_question:
                self.current_question = self.next_fetched_question
                self.next_fetched_question = None
                self.selected_option_idx = None
                self.state = STATE_QUESTION
            else:
                # Fallback to local
                self.current_question = self.qm._get_local_question(self.qm.category, self.qm.get_difficulty_for_level(self.level))
                self.selected_option_idx = None
                self.state = STATE_QUESTION

        # Blink cursor in text input
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    # ---------------------------------------------------------
    # Renderers
    # ---------------------------------------------------------
    def _render(self):
        self.screen.fill(COLOR_BG)

        # Ambient floating particles
        for p in self.particles:
            p.draw(self.screen)

        # Top Bar (always visible)
        self._render_top_header()

        # State-specific screens
        if self.state == STATE_MENU:
            self._render_menu()
        elif self.state == STATE_CATEGORY_SELECT:
            self._render_category_select()
        elif self.state == STATE_DIFFICULTY_SELECT:
            self._render_difficulty_select()
        elif self.state == STATE_LOADING:
            self._render_loading()
        elif self.state == STATE_QUESTION:
            self._render_question_screen()
        elif self.state == STATE_FEEDBACK:
            self._render_feedback_screen()
        elif self.state == STATE_LEVEL_UP:
            self._render_level_up_screen()
        elif self.state == STATE_VICTORY:
            self._render_victory_screen()
        elif self.state == STATE_GAME_OVER:
            self._render_game_over_screen()
        elif self.state == STATE_LEADERBOARD:
            self._render_leaderboard_screen()
        elif self.state == STATE_STATUS:
            self._render_status_screen()

        # Render floating popups
        for ft in self.floating_texts:
            ft.draw(self.screen, self.font_heading)

    def _render_top_header(self):
        """Render sound toggle and branding header."""
        # Mute button
        mute_rect = pygame.Rect(SCREEN_WIDTH - 60, 18, 42, 34)
        is_hover = mute_rect.collidepoint(pygame.mouse.get_pos())
        self._draw_glass_rect(self.screen, mute_rect, is_hover)
        icon_str = "MUTE" if not self.audio.muted else "UNMUTE"
        lbl = self.font_small.render(icon_str, True, COLOR_TEXT_SECONDARY if not self.audio.muted else COLOR_WRONG)
        self.screen.blit(lbl, (mute_rect.centerx - lbl.get_width() // 2, mute_rect.centery - lbl.get_height() // 2))

    # ---------------------------------------------------------
    # Menu Screen
    # ---------------------------------------------------------
    def _render_menu(self):
        title = self.font_title.render("QUIZ QUEST", True, COLOR_TEXT_PRIMARY)
        subtitle = self.font_subtitle.render("AI-Powered Trivia Adventure", True, COLOR_ACCENT_CYAN)

        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 70))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 125))

        btn_w, btn_h = 380, 48
        start_y = 180
        gap = 58

        buttons = [
            ("start", "START QUEST", COLOR_CORRECT),
            ("mode", f"Mode: {MODES_LIST[self.mode_index]}", COLOR_PURPLE),
            ("category", f"Category: {CATEGORIES_LIST[self.category_index]}", COLOR_ACCENT_CYAN),
            ("difficulty", f"Difficulty: {DIFFICULTIES_LIST[self.difficulty_index]}", COLOR_ACCENT_GOLD),
            ("leaderboard", "HIGH SCORES", COLOR_BLUE),
            ("status", "API STATUS", COLOR_TEXT_SECONDARY),
            ("exit", "EXIT GAME", COLOR_WRONG)
        ]

        self.menu_buttons.clear()
        mouse_pos = pygame.mouse.get_pos()

        for idx, (action, text, accent) in enumerate(buttons):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + idx * gap, btn_w, btn_h)
            self.menu_buttons[action] = rect
            is_hover = rect.collidepoint(mouse_pos)

            self._draw_glass_rect(self.screen, rect, is_hover, border_accent=accent if is_hover else None)

            # Left accent dot
            dot_color = accent if not is_hover else COLOR_TEXT_PRIMARY
            pygame.draw.circle(self.screen, dot_color, (rect.x + 22, rect.centery), 5)

            lbl = self.font_body.render(text, True, COLOR_TEXT_PRIMARY if not is_hover else COLOR_TEXT_PRIMARY)
            self.screen.blit(lbl, (rect.x + 40, rect.centery - lbl.get_height() // 2))

        # Bottom info tip
        hint = self.font_small.render("Controls: Mouse Click or Keys 1-4 / A-D | M to Mute | ESC to Return", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 35))

    # ---------------------------------------------------------
    # Category Select Screen
    # ---------------------------------------------------------
    def _render_category_select(self):
        title = self.font_heading.render("Select Trivia Realm", True, COLOR_ACCENT_CYAN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        self.category_rects = []
        mouse_pos = pygame.mouse.get_pos()
        btn_w, btn_h = 420, 44
        start_y = 110

        for idx, cat_name in enumerate(CATEGORIES_LIST):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + idx * 52, btn_w, btn_h)
            self.category_rects.append(rect)
            is_hover = rect.collidepoint(mouse_pos)
            is_active = (idx == self.category_index)

            border_col = COLOR_ACCENT_CYAN if (is_active or is_hover) else None
            self._draw_glass_rect(self.screen, rect, is_hover, border_accent=border_col)

            prefix = "✔  " if is_active else "•  "
            lbl = self.font_body.render(prefix + cat_name, True, COLOR_TEXT_PRIMARY if is_active else COLOR_TEXT_SECONDARY)
            self.screen.blit(lbl, (rect.x + 20, rect.centery - lbl.get_height() // 2))

    # ---------------------------------------------------------
    # Difficulty Select Screen
    # ---------------------------------------------------------
    def _render_difficulty_select(self):
        title = self.font_heading.render("Choose Difficulty Mode", True, COLOR_ACCENT_GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 70))

        subtitle = self.font_body.render("Progressive increases challenge from Level 1 (Easy) to Level 5 (Hard)", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 115))

        self.difficulty_rects = []
        mouse_pos = pygame.mouse.get_pos()
        btn_w, btn_h = 380, 56
        start_y = 180

        for idx, diff_name in enumerate(DIFFICULTIES_LIST):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + idx * 75, btn_w, btn_h)
            self.difficulty_rects.append(rect)
            is_hover = rect.collidepoint(mouse_pos)
            is_active = (idx == self.difficulty_index)

            border_col = COLOR_ACCENT_GOLD if (is_active or is_hover) else None
            self._draw_glass_rect(self.screen, rect, is_hover, border_accent=border_col)

            prefix = "★  " if is_active else "○  "
            lbl = self.font_heading.render(prefix + diff_name, True, COLOR_TEXT_PRIMARY if is_active else COLOR_TEXT_SECONDARY)
            self.screen.blit(lbl, (rect.x + 30, rect.centery - lbl.get_height() // 2))

    # ---------------------------------------------------------
    # HUD (Heads-Up Display)
    # ---------------------------------------------------------
    def _render_hud(self):
        # Level indicator
        lvl_str = f"LEVEL {self.level} / {self.max_levels}"
        lbl_lvl = self.font_heading.render(lvl_str, True, COLOR_ACCENT_CYAN)
        self.screen.blit(lbl_lvl, (40, 25))

        # Progress bar
        bar_x, bar_y, bar_w, bar_h = 40, 60, 200, 8
        pygame.draw.rect(self.screen, COLOR_BORDER, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        progress_ratio = (self.current_q_in_level) / float(self.questions_per_level)
        fill_w = int(bar_w * max(0.0, min(1.0, progress_ratio)))
        if fill_w > 0:
            pygame.draw.rect(self.screen, COLOR_ACCENT_CYAN, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        q_track = self.font_small.render(f"Question {min(self.current_q_in_level + 1, self.questions_per_level)} of {self.questions_per_level}", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(q_track, (40, 75))

        # Score in Gold (Center)
        score_val = f"SCORE: {self.score}"
        lbl_score = self.font_heading.render(score_val, True, COLOR_ACCENT_GOLD)
        self.screen.blit(lbl_score, (SCREEN_WIDTH // 2 - lbl_score.get_width() // 2, 25))

        # Lives in Hearts (Right side)
        lives_label = self.font_small.render("LIVES:", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(lives_label, (SCREEN_WIDTH - 240, 28))

        heart_x = SCREEN_WIDTH - 190
        for i in range(self.max_lives):
            is_active = (i < self.lives)
            heart_color = COLOR_WRONG if is_active else (60, 65, 75)
            # Draw visual heart symbol
            self._draw_heart_icon(self.screen, heart_x + i * 36, 36, 11, heart_color)

    def _draw_heart_icon(self, surface, x, y, size, color):
        """Draw geometric heart icon."""
        r = size // 2
        pygame.draw.circle(surface, color, (x - r // 2, y - r // 2), r)
        pygame.draw.circle(surface, color, (x + r // 2, y - r // 2), r)
        points = [(x - r - 1, y - 2), (x + r + 1, y - 2), (x, y + size)]
        pygame.draw.polygon(surface, color, points)

    # ---------------------------------------------------------
    # Loading State
    # ---------------------------------------------------------
    def _render_loading(self):
        self._render_hud()

        # Animated pulsing oracle spinner
        t = time.time()
        pulse = 14 + int(6 * math.sin(t * 5))

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20
        pygame.draw.circle(self.screen, COLOR_BORDER, (cx, cy), pulse + 12, width=2)
        pygame.draw.circle(self.screen, COLOR_ACCENT_CYAN, (cx, cy), pulse)

        lbl = self.font_heading.render("Consulting the Trivia Oracle...", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy + 45))

        source_info = "Generating original challenge via Gemini AI & OpenTDB"
        lbl_sub = self.font_small.render(source_info, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(lbl_sub, (cx - lbl_sub.get_width() // 2, cy + 85))

    # ---------------------------------------------------------
    # Question Screen
    # ---------------------------------------------------------
    def _render_question_screen(self):
        if not self.current_question:
            return

        self._render_hud()

        # Source Badge
        source_name = self.current_question.get("source", "Trivia")
        badge_color = COLOR_PURPLE if "Gemini" in source_name else (COLOR_BLUE if "Open" in source_name else COLOR_TEAL)
        badge_icon = "🤖 " if "Gemini" in source_name else ("🌐 " if "Open" in source_name else "💾 ")
        badge_text = f"{badge_icon}{source_name.upper()}"

        badge_w, badge_h = 190, 28
        badge_rect = pygame.Rect(SCREEN_WIDTH // 2 - badge_w // 2, 85, badge_w, badge_h)
        pygame.draw.rect(self.screen, COLOR_BG_CARD, badge_rect, border_radius=14)
        pygame.draw.rect(self.screen, badge_color, badge_rect, width=1, border_radius=14)
        lbl_badge = self.font_badge.render(badge_text, True, badge_color)
        self.screen.blit(lbl_badge, (badge_rect.centerx - lbl_badge.get_width() // 2, badge_rect.centery - lbl_badge.get_height() // 2))

        # Question Card Container
        q_card_w, q_card_h = 920, 150
        q_card_rect = pygame.Rect(SCREEN_WIDTH // 2 - q_card_w // 2, 125, q_card_w, q_card_h)
        self._draw_glass_rect(self.screen, q_card_rect, is_hover=False)

        # Category & Difficulty Subtitle
        cat_str = self.current_question.get("category", "General")
        diff_str = self.current_question.get("difficulty", "medium").upper()
        meta_str = f"{cat_str}  •  {diff_str}"
        lbl_meta = self.font_small.render(meta_str, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(lbl_meta, (q_card_rect.x + 24, q_card_rect.y + 16))

        # Word-wrapped Question Text
        q_text = self.current_question.get("question", "")
        self._render_wrapped_text(self.screen, q_text, self.font_heading, COLOR_TEXT_PRIMARY,
                                  q_card_rect.x + 24, q_card_rect.y + 44, q_card_w - 48, max_lines=3)

        # 4 Option Cards
        options = self.current_question.get("options", [])
        self.option_rects = []
        mouse_pos = pygame.mouse.get_pos()

        opt_w, opt_h = 445, 90
        grid_positions = [
            (SCREEN_WIDTH // 2 - opt_w - 15, 300),  # Option A (top left)
            (SCREEN_WIDTH // 2 + 15, 300),          # Option B (top right)
            (SCREEN_WIDTH // 2 - opt_w - 15, 415),  # Option C (bottom left)
            (SCREEN_WIDTH // 2 + 15, 415),          # Option D (bottom right)
        ]

        letters = ["A", "B", "C", "D"]
        for idx in range(min(4, len(options))):
            gx, gy = grid_positions[idx]
            rect = pygame.Rect(gx, gy, opt_w, opt_h)
            self.option_rects.append(rect)
            is_hover = rect.collidepoint(mouse_pos)

            self._draw_glass_rect(self.screen, rect, is_hover, border_accent=COLOR_ACCENT_CYAN if is_hover else None)

            # Option letter badge circle
            circle_color = COLOR_ACCENT_CYAN if is_hover else COLOR_BORDER
            pygame.draw.circle(self.screen, circle_color, (rect.x + 36, rect.centery), 18)
            lbl_letter = self.font_heading.render(letters[idx], True, COLOR_BG if is_hover else COLOR_TEXT_PRIMARY)
            self.screen.blit(lbl_letter, (rect.x + 36 - lbl_letter.get_width() // 2, rect.centery - lbl_letter.get_height() // 2))

            # Option text (wrapped)
            opt_str = options[idx]
            self._render_wrapped_text(self.screen, opt_str, self.font_body, COLOR_TEXT_PRIMARY,
                                      rect.x + 68, rect.y + 18, opt_w - 80, max_lines=2)

        # Bottom Controls reminder
        controls_msg = "Select using Mouse Click or press keys [A, B, C, D] / [1, 2, 3, 4] | ESC for Menu"
        lbl_ctrl = self.font_small.render(controls_msg, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(lbl_ctrl, (SCREEN_WIDTH // 2 - lbl_ctrl.get_width() // 2, SCREEN_HEIGHT - 35))

    # ---------------------------------------------------------
    # Feedback Screen (After answering)
    # ---------------------------------------------------------
    def _render_feedback_screen(self):
        self._render_hud()

        # Banner Title
        banner_color = COLOR_CORRECT if self.is_correct else COLOR_WRONG
        lbl_msg = self.font_title.render(self.feedback_message, True, banner_color)
        self.screen.blit(lbl_msg, (SCREEN_WIDTH // 2 - lbl_msg.get_width() // 2, 95))

        # Show Options with Correct / Incorrect highlights
        options = self.current_question.get("options", [])
        correct_ans = self.current_question.get("correct_answer", "").strip().lower()

        opt_w, opt_h = 445, 75
        grid_positions = [
            (SCREEN_WIDTH // 2 - opt_w - 15, 170),
            (SCREEN_WIDTH // 2 + 15, 170),
            (SCREEN_WIDTH // 2 - opt_w - 15, 260),
            (SCREEN_WIDTH // 2 + 15, 260),
        ]

        letters = ["A", "B", "C", "D"]
        for idx in range(min(4, len(options))):
            gx, gy = grid_positions[idx]
            rect = pygame.Rect(gx, gy, opt_w, opt_h)
            opt_str = options[idx]

            is_this_correct = (opt_str.strip().lower() == correct_ans)
            is_this_chosen = (idx == self.selected_option_idx)

            if is_this_correct:
                border_col = COLOR_CORRECT
                bg_col = (18, 50, 32)
            elif is_this_chosen and not self.is_correct:
                border_col = COLOR_WRONG
                bg_col = (55, 20, 24)
            else:
                border_col = COLOR_BORDER
                bg_col = COLOR_BG_CARD

            pygame.draw.rect(self.screen, bg_col, rect, border_radius=12)
            pygame.draw.rect(self.screen, border_col, rect, width=2, border_radius=12)

            tag = " ✔ (Correct)" if is_this_correct else (" ✖ (Your Pick)" if (is_this_chosen and not self.is_correct) else "")
            display_text = f"{letters[idx]}. {opt_str}{tag}"
            self._render_wrapped_text(self.screen, display_text, self.font_body, COLOR_TEXT_PRIMARY,
                                      rect.x + 20, rect.y + 16, opt_w - 40, max_lines=2)

        # Educational Explanation Card
        expl_w, expl_h = 920, 160
        expl_rect = pygame.Rect(SCREEN_WIDTH // 2 - expl_w // 2, 360, expl_w, expl_h)
        self._draw_glass_rect(self.screen, expl_rect, is_hover=False, border_accent=COLOR_ACCENT_CYAN)

        lbl_hdr = self.font_heading.render("💡 Knowledge Insight:", True, COLOR_ACCENT_CYAN)
        self.screen.blit(lbl_hdr, (expl_rect.x + 24, expl_rect.y + 16))

        explanation_text = self.current_question.get("explanation", "The answer is verified by our trivia engine.")
        self._render_wrapped_text(self.screen, explanation_text, self.font_body, COLOR_TEXT_PRIMARY,
                                  expl_rect.x + 24, expl_rect.y + 54, expl_w - 48, max_lines=4)

        # Continue Button
        btn_w, btn_h = 320, 52
        self.continue_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, 555, btn_w, btn_h)
        is_hover = self.continue_btn_rect.collidepoint(pygame.mouse.get_pos())
        self._draw_glass_rect(self.screen, self.continue_btn_rect, is_hover, border_accent=COLOR_CORRECT)

        lbl_cont = self.font_heading.render("CONTINUE  ➔", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl_cont, (self.continue_btn_rect.centerx - lbl_cont.get_width() // 2,
                                    self.continue_btn_rect.centery - lbl_cont.get_height() // 2))

        sub_tip = self.font_small.render("Press SPACE or RETURN to advance", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(sub_tip, (SCREEN_WIDTH // 2 - sub_tip.get_width() // 2, 620))

    # ---------------------------------------------------------
    # Level Up Screen
    # ---------------------------------------------------------
    def _render_level_up_screen(self):
        title = self.font_title.render("LEVEL COMPLETE!", True, COLOR_ACCENT_GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 130))

        sub = self.font_heading.render(f"Entering Level {self.level} of {self.max_levels}", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 200))

        diff_name = self.qm.get_difficulty_for_level(self.level).upper()
        diff_info = self.font_body.render(f"Next Difficulty: {diff_name}", True, COLOR_ACCENT_CYAN)
        self.screen.blit(diff_info, (SCREEN_WIDTH // 2 - diff_info.get_width() // 2, 250))

        # Stats Card
        card_w, card_h = 480, 140
        rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, 305, card_w, card_h)
        self._draw_glass_rect(self.screen, rect, is_hover=False)

        stat1 = self.font_body.render(f"Current Score: {self.score}", True, COLOR_ACCENT_GOLD)
        stat2 = self.font_body.render(f"Lives Remaining: {self.lives} / {self.max_lives}", True, COLOR_WRONG)
        stat3 = self.font_body.render(f"Questions Answered: {self.total_questions_answered}", True, COLOR_TEXT_SECONDARY)

        self.screen.blit(stat1, (rect.x + 30, rect.y + 24))
        self.screen.blit(stat2, (rect.x + 30, rect.y + 60))
        self.screen.blit(stat3, (rect.x + 30, rect.y + 96))

        # Continue button
        btn_w, btn_h = 320, 52
        self.level_up_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, 485, btn_w, btn_h)
        is_hover = self.level_up_btn_rect.collidepoint(pygame.mouse.get_pos())
        self._draw_glass_rect(self.screen, self.level_up_btn_rect, is_hover, border_accent=COLOR_ACCENT_CYAN)

        lbl = self.font_heading.render("PROCEED TO NEXT LEVEL ➔", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl, (self.level_up_btn_rect.centerx - lbl.get_width() // 2,
                               self.level_up_btn_rect.centery - lbl.get_height() // 2))

    # ---------------------------------------------------------
    # Victory Screen
    # ---------------------------------------------------------
    def _render_victory_screen(self):
        title = self.font_title.render("QUEST CONQUERED! 🏆", True, COLOR_ACCENT_GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        sub = self.font_heading.render("All 5 Levels Mastered – You are a Grand Scholar!", True, COLOR_CORRECT)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 140))

        # Victory stats card
        card_w, card_h = 520, 160
        rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, 195, card_w, card_h)
        self._draw_glass_rect(self.screen, rect, is_hover=False, border_accent=COLOR_ACCENT_GOLD)

        s1 = self.font_heading.render(f"FINAL SCORE: {self.score}", True, COLOR_ACCENT_GOLD)
        s2 = self.font_body.render(f"Survival Bonus: +{self.lives * 20} pts ({self.lives} hearts retained)", True, COLOR_CORRECT)
        s3 = self.font_body.render(f"Mode: {MODES_LIST[self.mode_index]}  |  Category: {CATEGORIES_LIST[self.category_index]}", True, COLOR_TEXT_SECONDARY)

        self.screen.blit(s1, (rect.centerx - s1.get_width() // 2, rect.y + 24))
        self.screen.blit(s2, (rect.centerx - s2.get_width() // 2, rect.y + 74))
        self.screen.blit(s3, (rect.centerx - s3.get_width() // 2, rect.y + 114))

        # Enter Name for Leaderboard
        self._render_name_input_box(390)

    # ---------------------------------------------------------
    # Game Over Screen
    # ---------------------------------------------------------
    def _render_game_over_screen(self):
        title = self.font_title.render("QUEST FAILED", True, COLOR_WRONG)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 90))

        sub = self.font_heading.render(f"Out of lives at Level {self.level} of {self.max_levels}", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 150))

        card_w, card_h = 480, 120
        rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, 205, card_w, card_h)
        self._draw_glass_rect(self.screen, rect, is_hover=False)

        s1 = self.font_heading.render(f"FINAL SCORE: {self.score}", True, COLOR_ACCENT_GOLD)
        s2 = self.font_body.render(f"Questions Answered: {self.total_questions_answered}", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(s1, (rect.centerx - s1.get_width() // 2, rect.y + 24))
        self.screen.blit(s2, (rect.centerx - s2.get_width() // 2, rect.y + 70))

        self._render_name_input_box(365)

    def _render_name_input_box(self, start_y: int):
        """Render player name input field and submit buttons."""
        lbl_prompt = self.font_body.render("Enter Your Name for the Hall of Fame:", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl_prompt, (SCREEN_WIDTH // 2 - lbl_prompt.get_width() // 2, start_y))

        box_w, box_h = 360, 48
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - box_w // 2, start_y + 35, box_w, box_h)
        pygame.draw.rect(self.screen, COLOR_BG_CARD, box_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_ACCENT_CYAN, box_rect, width=2, border_radius=8)

        cursor_str = "|" if self.cursor_visible else ""
        name_disp = self.player_name + cursor_str
        lbl_name = self.font_heading.render(name_disp, True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl_name, (box_rect.x + 18, box_rect.centery - lbl_name.get_height() // 2))

        # Submit Button
        btn_w, btn_h = 240, 48
        self.submit_score_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + 105, btn_w, btn_h)
        is_hover = self.submit_score_btn_rect.collidepoint(pygame.mouse.get_pos())
        self._draw_glass_rect(self.screen, self.submit_score_btn_rect, is_hover, border_accent=COLOR_CORRECT)

        lbl_sub = self.font_heading.render("SAVE SCORE ➔", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl_sub, (self.submit_score_btn_rect.centerx - lbl_sub.get_width() // 2,
                                   self.submit_score_btn_rect.centery - lbl_sub.get_height() // 2))

        # Main Menu button
        self.menu_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 160 // 2, start_y + 175, 160, 36)
        is_mhover = self.menu_btn_rect.collidepoint(pygame.mouse.get_pos())
        self._draw_glass_rect(self.screen, self.menu_btn_rect, is_mhover)
        lbl_m = self.font_small.render("Back to Menu", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(lbl_m, (self.menu_btn_rect.centerx - lbl_m.get_width() // 2,
                                 self.menu_btn_rect.centery - lbl_m.get_height() // 2))

    # ---------------------------------------------------------
    # Leaderboard Screen
    # ---------------------------------------------------------
    def _render_leaderboard_screen(self):
        title = self.font_title.render("HALL OF FAME", True, COLOR_ACCENT_GOLD)
        subtitle = self.font_small.render("Top 10 Adventurers Across All Sessions", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 45))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 95))

        entries = get_top_entries(limit=10)

        table_w = 880
        table_x = SCREEN_WIDTH // 2 - table_w // 2
        start_y = 135

        # Table Header
        header_rect = pygame.Rect(table_x, start_y, table_w, 36)
        pygame.draw.rect(self.screen, COLOR_BORDER, header_rect, border_radius=6)

        cols = [
            ("RANK", table_x + 20),
            ("PLAYER", table_x + 110),
            ("SCORE", table_x + 360),
            ("LEVEL", table_x + 480),
            ("MODE", table_x + 600),
            ("DATE", table_x + 750)
        ]

        for col_name, cx in cols:
            lbl = self.font_badge.render(col_name, True, COLOR_TEXT_PRIMARY)
            self.screen.blit(lbl, (cx, start_y + 10))

        # Table Rows
        row_y = start_y + 44
        if not entries:
            empty_lbl = self.font_body.render("No scores recorded yet. Be the first champion!", True, COLOR_TEXT_SECONDARY)
            self.screen.blit(empty_lbl, (SCREEN_WIDTH // 2 - empty_lbl.get_width() // 2, row_y + 50))
        else:
            medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
            for idx, entry in enumerate(entries):
                row_rect = pygame.Rect(table_x, row_y + idx * 42, table_w, 36)
                bg_color = (20, 25, 34) if idx % 2 == 0 else (15, 19, 27)
                pygame.draw.rect(self.screen, bg_color, row_rect, border_radius=6)

                rank_str = medals[idx] if idx < 3 else f"#{idx + 1}"
                rank_col = COLOR_ACCENT_GOLD if idx == 0 else (COLOR_TEXT_PRIMARY if idx < 3 else COLOR_TEXT_SECONDARY)

                r_lbl = self.font_body.render(rank_str, True, rank_col)
                n_lbl = self.font_body.render(entry.get("name", "Unknown"), True, COLOR_TEXT_PRIMARY)
                s_lbl = self.font_heading.render(str(entry.get("score", 0)), True, COLOR_ACCENT_GOLD)
                l_lbl = self.font_body.render(f"Lvl {entry.get('level', 1)}", True, COLOR_ACCENT_CYAN)
                m_lbl = self.font_small.render(entry.get("mode", "Mixed"), True, COLOR_TEXT_SECONDARY)
                d_lbl = self.font_small.render(entry.get("date", ""), True, COLOR_TEXT_SECONDARY)

                y_off = row_rect.y + 7
                self.screen.blit(r_lbl, (table_x + 20, y_off))
                self.screen.blit(n_lbl, (table_x + 110, y_off))
                self.screen.blit(s_lbl, (table_x + 360, y_off - 4))
                self.screen.blit(l_lbl, (table_x + 480, y_off))
                self.screen.blit(m_lbl, (table_x + 600, y_off + 2))
                self.screen.blit(d_lbl, (table_x + 750, y_off + 2))

        # Back button
        self.back_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180 // 2, SCREEN_HEIGHT - 65, 180, 44)
        is_hover = self.back_btn_rect.collidepoint(pygame.mouse.get_pos())
        self._draw_glass_rect(self.screen, self.back_btn_rect, is_hover)
        lbl_b = self.font_heading.render("➔ BACK", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl_b, (self.back_btn_rect.centerx - lbl_b.get_width() // 2,
                                 self.back_btn_rect.centery - lbl_b.get_height() // 2))

    # ---------------------------------------------------------
    # Status Screen (Live API Health)
    # ---------------------------------------------------------
    def _render_status_screen(self):
        title = self.font_title.render("SYSTEM & API STATUS", True, COLOR_ACCENT_CYAN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 70))

        status_dict = self.qm.get_api_status()

        services = [
            ("Google Gemini AI API", status_dict["gemini"], "Dynamic questions & contextual reasoning", COLOR_PURPLE),
            ("Open Trivia Database", status_dict["opentdb"], "Public REST Trivia API (opentdb.com)", COLOR_BLUE),
            ("Local Quest Vault", status_dict["local"], "Offline resilient JSON fallback dataset", COLOR_TEAL)
        ]

        start_y = 170
        card_w, card_h = 680, 90

        for idx, (svc_name, is_online, desc, accent) in enumerate(services):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, start_y + idx * 115, card_w, card_h)
            self._draw_glass_rect(self.screen, rect, is_hover=False, border_accent=accent)

            lbl_name = self.font_heading.render(svc_name, True, COLOR_TEXT_PRIMARY)
            lbl_desc = self.font_small.render(desc, True, COLOR_TEXT_SECONDARY)

            self.screen.blit(lbl_name, (rect.x + 28, rect.y + 20))
            self.screen.blit(lbl_desc, (rect.x + 28, rect.y + 54))

            # Status pill
            pill_text = "READY / ONLINE" if is_online else "OFFLINE / FALLBACK"
            pill_col = COLOR_CORRECT if is_online else COLOR_WRONG
            lbl_pill = self.font_badge.render(pill_text, True, pill_col)
            self.screen.blit(lbl_pill, (rect.right - lbl_pill.get_width() - 28, rect.centery - lbl_pill.get_height() // 2))

        # Back button
        self.back_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180 // 2, SCREEN_HEIGHT - 90, 180, 44)
        is_hover = self.back_btn_rect.collidepoint(pygame.mouse.get_pos())
        self._draw_glass_rect(self.screen, self.back_btn_rect, is_hover)
        lbl_b = self.font_heading.render("➔ BACK", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lbl_b, (self.back_btn_rect.centerx - lbl_b.get_width() // 2,
                                 self.back_btn_rect.centery - lbl_b.get_height() // 2))

    # ---------------------------------------------------------
    # Utility Drawing Helpers
    # ---------------------------------------------------------
    def _draw_glass_rect(self, surface, rect: pygame.Rect, is_hover: bool = False, border_accent=None):
        """Draw sleek glassmorphic container with rounded corners and subtle highlight."""
        bg = (28, 33, 44) if is_hover else COLOR_BG_CARD
        border = border_accent if border_accent else (COLOR_BORDER_HOVER if is_hover else COLOR_BORDER)
        pygame.draw.rect(surface, bg, rect, border_radius=12)
        pygame.draw.rect(surface, border, rect, width=2 if is_hover else 1, border_radius=12)

    def _render_wrapped_text(self, surface, text: str, font, color, x: int, y: int, max_width: int, max_lines: int = 3):
        """Word wrap text within bounds cleanly."""
        words = text.split(" ")
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        line_height = font.get_linesize()
        for idx, line_str in enumerate(lines[:max_lines]):
            # If on last line and there are more lines, append ellipsis
            if idx == max_lines - 1 and len(lines) > max_lines:
                line_str += "..."
            rendered = font.render(line_str, True, color)
            surface.blit(rendered, (x, y + idx * line_height))
