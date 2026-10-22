"""
Quiz Quest - Procedural Audio Manager
Generates retro-modern sound effects entirely in memory using pure Python waveforms.
Zero external audio files required!
"""

import array
import math
import pygame


class AudioManager:
    """Generates and plays dynamic sound effects."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.muted = False
        self.enabled = False
        self.sounds = {}
        self._init_mixer()

    def _init_mixer(self):
        """Initialize Pygame mixer and generate sound buffers."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self._generate_sounds()
            self.enabled = True
        except Exception as e:
            print(f"[AudioManager] Audio initialization skipped: {e}")
            self.enabled = False

    def _build_wave(self, tone_specs: list, decay_factor: float = 3.0) -> pygame.mixer.Sound:
        """
        Build an in-memory Sound from a list of (frequency, duration_ms) tuples.
        """
        raw_samples = array.array("h")
        for freq, duration_ms in tone_specs:
            num_samples = int(self.sample_rate * (duration_ms / 1000.0))
            for i in range(num_samples):
                t = i / self.sample_rate
                # Apply envelope to prevent audio clicking
                progress = i / max(1, num_samples)
                envelope = math.exp(-decay_factor * progress)
                if progress < 0.05:  # Attack
                    envelope *= (progress / 0.05)

                sample_val = int(14000 * envelope * math.sin(2.0 * math.pi * freq * t))
                # Clamp within 16-bit signed integer limits
                sample_val = max(-32767, min(32767, sample_val))
                raw_samples.append(sample_val)

        return pygame.mixer.Sound(buffer=raw_samples)

    def _generate_sounds(self):
        """Pre-render procedural sounds."""
        try:
            # 1. Click / Select blip
            self.sounds["click"] = self._build_wave([(880, 45)], decay_factor=8.0)

            # 2. Correct chime (rising major chord arpeggio)
            self.sounds["correct"] = self._build_wave([(523.25, 70), (659.25, 80), (783.99, 140)], decay_factor=2.5)

            # 3. Wrong buzz (descending dissonant buzz)
            self.sounds["wrong"] = self._build_wave([(220, 100), (174.61, 140), (130.81, 180)], decay_factor=2.0)

            # 4. Level Up fanfare
            self.sounds["level_up"] = self._build_wave([
                (523.25, 80), (659.25, 80), (783.99, 80), (1046.50, 240)
            ], decay_factor=2.0)

            # 5. Victory melody
            self.sounds["victory"] = self._build_wave([
                (523.25, 100), (659.25, 100), (783.99, 100), (1046.50, 150),
                (880, 100), (1046.50, 350)
            ], decay_factor=1.8)

            # 6. Game Over sad chord
            self.sounds["game_over"] = self._build_wave([
                (392.00, 150), (369.99, 150), (329.63, 180), (293.66, 320)
            ], decay_factor=2.0)
        except Exception as e:
            print(f"[AudioManager] Error generating procedural waves: {e}")

    def play(self, sound_name: str):
        """Play sound by name if unmuted."""
        if self.muted or not self.enabled:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def toggle_mute(self) -> bool:
        """Toggle mute state and return new state."""
        self.muted = not self.muted
        return self.muted
