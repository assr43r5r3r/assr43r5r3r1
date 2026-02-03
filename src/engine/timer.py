"""
Timer utilities for frame-accurate timing.
"""

import time
from typing import Optional


class Timer:
    """
    General-purpose timer for tracking elapsed time.
    """
    
    def __init__(self):
        self._start_time: float = 0.0
        self._paused_time: float = 0.0
        self._is_paused: bool = False
        self._is_running: bool = False
    
    def start(self) -> None:
        """Start or resume the timer."""
        if not self._is_running:
            self._start_time = time.perf_counter()
            self._is_running = True
            self._is_paused = False
        elif self._is_paused:
            # Resume from pause
            pause_duration = time.perf_counter() - self._paused_time
            self._start_time += pause_duration
            self._is_paused = False
    
    def pause(self) -> None:
        """Pause the timer."""
        if self._is_running and not self._is_paused:
            self._paused_time = time.perf_counter()
            self._is_paused = True
    
    def reset(self) -> None:
        """Reset the timer to zero."""
        self._start_time = time.perf_counter()
        self._paused_time = 0.0
        self._is_paused = False
    
    def stop(self) -> None:
        """Stop the timer completely."""
        self._is_running = False
        self._is_paused = False
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if not self._is_running:
            return 0.0
        if self._is_paused:
            return self._paused_time - self._start_time
        return time.perf_counter() - self._start_time
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed * 1000.0
    
    @property
    def is_running(self) -> bool:
        """Check if timer is running."""
        return self._is_running and not self._is_paused


class FrameTimer:
    """
    Frame-based timer for game logic.
    Counts frames rather than real time for deterministic behavior.
    """
    
    def __init__(self, duration_frames: int):
        """
        Initialize frame timer.
        
        Args:
            duration_frames: Number of frames until timer expires
        """
        self._duration = duration_frames
        self._current = 0
        self._is_active = False
    
    def start(self) -> None:
        """Start or restart the timer."""
        self._current = 0
        self._is_active = True
    
    def stop(self) -> None:
        """Stop the timer."""
        self._is_active = False
        self._current = 0
    
    def tick(self) -> bool:
        """
        Advance timer by one frame.
        
        Returns:
            True if timer just expired this frame
        """
        if not self._is_active:
            return False
        
        self._current += 1
        if self._current >= self._duration:
            self._is_active = False
            return True
        return False
    
    def reset(self) -> None:
        """Reset timer without stopping."""
        self._current = 0
    
    @property
    def remaining(self) -> int:
        """Get remaining frames."""
        if not self._is_active:
            return 0
        return max(0, self._duration - self._current)
    
    @property
    def progress(self) -> float:
        """Get progress as 0.0 to 1.0."""
        if self._duration == 0:
            return 1.0
        return min(1.0, self._current / self._duration)
    
    @property
    def is_active(self) -> bool:
        """Check if timer is active."""
        return self._is_active
    
    def set_duration(self, frames: int) -> None:
        """Change the duration."""
        self._duration = frames


class CooldownTimer:
    """
    Timer that tracks cooldown periods.
    """
    
    def __init__(self, cooldown_frames: int):
        self._cooldown = cooldown_frames
        self._remaining = 0
    
    def trigger(self) -> None:
        """Start the cooldown."""
        self._remaining = self._cooldown
    
    def tick(self) -> None:
        """Advance timer by one frame."""
        if self._remaining > 0:
            self._remaining -= 1
    
    @property
    def is_ready(self) -> bool:
        """Check if cooldown has completed."""
        return self._remaining <= 0
    
    @property
    def remaining(self) -> int:
        """Get remaining cooldown frames."""
        return self._remaining
