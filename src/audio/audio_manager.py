"""
Audio manager for music and sound effects.
"""

from typing import Dict, Optional
from pathlib import Path
import os

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


class AudioManager:
    """
    Manages music and sound effects.
    
    Provides volume control and event-based sound playback.
    """
    
    def __init__(
        self,
        master_volume: float = 0.8,
        music_volume: float = 0.5,
        sfx_volume: float = 0.7
    ):
        """
        Initialize audio manager.
        
        Args:
            master_volume: Master volume (0.0 to 1.0)
            music_volume: Music volume (0.0 to 1.0)
            sfx_volume: Sound effects volume (0.0 to 1.0)
        """
        self._master_volume = master_volume
        self._music_volume = music_volume
        self._sfx_volume = sfx_volume
        
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._music_playing = False
        self._initialized = False
        
        self._init_audio()
    
    def _init_audio(self) -> None:
        """Initialize pygame audio."""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
        except pygame.error:
            print("Warning: Audio initialization failed")
            self._initialized = False
    
    def load_sound(self, name: str, path: str) -> bool:
        """
        Load a sound effect.
        
        Args:
            name: Name to reference the sound
            path: Path to sound file
        
        Returns:
            True if loaded successfully
        """
        if not self._initialized:
            return False
        
        try:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                self._sounds[name] = sound
                return True
        except pygame.error:
            pass
        
        return False
    
    def play_sound(self, name: str) -> None:
        """
        Play a sound effect.
        
        Args:
            name: Name of the sound to play
        """
        if not self._initialized:
            return
        
        sound = self._sounds.get(name)
        if sound:
            volume = self._master_volume * self._sfx_volume
            sound.set_volume(volume)
            sound.play()
    
    def load_music(self, path: str) -> bool:
        """
        Load background music.
        
        Args:
            path: Path to music file
        
        Returns:
            True if loaded successfully
        """
        if not self._initialized:
            return False
        
        try:
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                return True
        except pygame.error:
            pass
        
        return False
    
    def play_music(self, loops: int = -1) -> None:
        """
        Start playing music.
        
        Args:
            loops: Number of loops (-1 for infinite)
        """
        if not self._initialized:
            return
        
        try:
            volume = self._master_volume * self._music_volume
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
            self._music_playing = True
        except pygame.error:
            pass
    
    def stop_music(self) -> None:
        """Stop playing music."""
        if self._initialized:
            pygame.mixer.music.stop()
            self._music_playing = False
    
    def pause_music(self) -> None:
        """Pause music."""
        if self._initialized:
            pygame.mixer.music.pause()
    
    def unpause_music(self) -> None:
        """Unpause music."""
        if self._initialized:
            pygame.mixer.music.unpause()
    
    def set_master_volume(self, volume: float) -> None:
        """Set master volume."""
        self._master_volume = max(0.0, min(1.0, volume))
        self._update_volumes()
    
    def set_music_volume(self, volume: float) -> None:
        """Set music volume."""
        self._music_volume = max(0.0, min(1.0, volume))
        self._update_volumes()
    
    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume."""
        self._sfx_volume = max(0.0, min(1.0, volume))
    
    def _update_volumes(self) -> None:
        """Update music volume based on current settings."""
        if self._initialized and self._music_playing:
            volume = self._master_volume * self._music_volume
            pygame.mixer.music.set_volume(volume)
    
    @property
    def master_volume(self) -> float:
        return self._master_volume
    
    @property
    def music_volume(self) -> float:
        return self._music_volume
    
    @property
    def sfx_volume(self) -> float:
        return self._sfx_volume
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    # Convenience methods for game events
    def play_move(self) -> None:
        """Play piece move sound."""
        self.play_sound("move")
    
    def play_rotate(self) -> None:
        """Play rotation sound."""
        self.play_sound("rotate")
    
    def play_lock(self) -> None:
        """Play piece lock sound."""
        self.play_sound("lock")
    
    def play_hold(self) -> None:
        """Play hold sound."""
        self.play_sound("hold")
    
    def play_hard_drop(self) -> None:
        """Play hard drop sound."""
        self.play_sound("hard_drop")
    
    def play_line_clear(self, lines: int) -> None:
        """Play line clear sound based on lines cleared."""
        if lines == 4:
            self.play_sound("tetris")
        elif lines >= 1:
            self.play_sound("clear")
    
    def play_tspin(self) -> None:
        """Play T-Spin sound."""
        self.play_sound("tspin")
    
    def play_combo(self) -> None:
        """Play combo sound."""
        self.play_sound("combo")
    
    def play_level_up(self) -> None:
        """Play level up sound."""
        self.play_sound("level_up")
    
    def play_game_over(self) -> None:
        """Play game over sound."""
        self.play_sound("game_over")
    
    def play_menu_select(self) -> None:
        """Play menu selection sound."""
        self.play_sound("menu_select")
    
    def play_menu_move(self) -> None:
        """Play menu navigation sound."""
        self.play_sound("menu_move")


def create_placeholder_sounds(audio: AudioManager) -> None:
    """
    Create placeholder sounds using pygame's built-in synthesis.
    Used when no sound files are available.
    """
    if not audio.is_initialized:
        return
    
    try:
        import array
        import math
        
        sample_rate = 44100
        
        def create_beep(frequency: float, duration: float, volume: float = 0.3) -> pygame.mixer.Sound:
            """Create a simple beep sound."""
            n_samples = int(sample_rate * duration)
            buf = array.array('h', [0] * n_samples)
            
            for i in range(n_samples):
                t = i / sample_rate
                # Envelope
                env = min(1.0, min(t / 0.01, (duration - t) / 0.05))
                # Sine wave
                val = int(32767 * volume * env * math.sin(2 * math.pi * frequency * t))
                buf[i] = val
            
            return pygame.mixer.Sound(buffer=buf)
        
        def create_chord(frequencies: list, duration: float, volume: float = 0.3) -> pygame.mixer.Sound:
            """Create a chord sound."""
            n_samples = int(sample_rate * duration)
            buf = array.array('h', [0] * n_samples)
            
            for i in range(n_samples):
                t = i / sample_rate
                env = min(1.0, min(t / 0.02, (duration - t) / 0.1))
                val = 0
                for freq in frequencies:
                    val += math.sin(2 * math.pi * freq * t)
                val = int(32767 * volume * env * val / len(frequencies))
                buf[i] = max(-32767, min(32767, val))
            
            return pygame.mixer.Sound(buffer=buf)
        
        # Create sounds
        audio._sounds["move"] = create_beep(300, 0.05, 0.2)
        audio._sounds["rotate"] = create_beep(400, 0.08, 0.25)
        audio._sounds["lock"] = create_beep(200, 0.1, 0.3)
        audio._sounds["hold"] = create_beep(350, 0.1, 0.25)
        audio._sounds["hard_drop"] = create_beep(150, 0.15, 0.35)
        audio._sounds["clear"] = create_beep(500, 0.2, 0.3)
        audio._sounds["tetris"] = create_beep(600, 0.3, 0.4)
        audio._sounds["tspin"] = create_beep(550, 0.25, 0.35)
        audio._sounds["combo"] = create_beep(450, 0.15, 0.3)
        audio._sounds["level_up"] = create_beep(700, 0.4, 0.35)
        audio._sounds["game_over"] = create_beep(100, 0.5, 0.4)
        audio._sounds["menu_select"] = create_beep(400, 0.1, 0.25)
        audio._sounds["menu_move"] = create_beep(300, 0.05, 0.2)
        
        # New sounds for countdown and stage
        audio._sounds["countdown"] = create_beep(440, 0.15, 0.4)
        audio._sounds["go"] = create_chord([523, 659, 784], 0.4, 0.5)  # C major chord
        audio._sounds["stage_up"] = create_chord([440, 554, 659], 0.5, 0.45)  # A major chord
        
    except Exception:
        # Silently fail if sound creation fails
        pass
