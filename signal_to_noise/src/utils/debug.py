"""
Debug overlay and profiling utilities.

Provides real-time performance monitoring and debug information display.
"""

import time
from typing import Dict, List, Any, Optional, Deque
from collections import deque
from dataclasses import dataclass, field


@dataclass
class SystemTiming:
    """Timing data for a single system."""
    name: str
    last_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    max_time_ms: float = 0.0
    samples: Deque[float] = field(default_factory=lambda: deque(maxlen=60))
    
    def add_sample(self, time_ms: float) -> None:
        """Add a timing sample."""
        self.samples.append(time_ms)
        self.last_time_ms = time_ms
        self.avg_time_ms = sum(self.samples) / len(self.samples)
        self.max_time_ms = max(self.max_time_ms, time_ms)


class DebugOverlay:
    """
    Debug overlay for displaying performance metrics and game state.
    
    Shows FPS, system timings, entity counts, and custom debug info.
    """
    
    def __init__(self):
        self.enabled: bool = False
        self.fps_samples: Deque[float] = deque(maxlen=60)
        self.system_timings: Dict[str, SystemTiming] = {}
        self.custom_stats: Dict[str, Any] = {}
        self.last_frame_time: float = time.perf_counter()
        self._frame_count: int = 0
        self._last_fps_update: float = time.perf_counter()
        self._current_fps: float = 0.0
        
    def toggle(self) -> None:
        """Toggle debug overlay visibility."""
        self.enabled = not self.enabled
    
    def begin_frame(self) -> None:
        """Call at the start of each frame."""
        current_time = time.perf_counter()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        if frame_time > 0:
            self.fps_samples.append(1.0 / frame_time)
        
        self._frame_count += 1
        if current_time - self._last_fps_update >= 1.0:
            self._current_fps = self._frame_count / (current_time - self._last_fps_update)
            self._frame_count = 0
            self._last_fps_update = current_time
    
    def start_system_timing(self, system_name: str) -> float:
        """Start timing a system. Returns start time."""
        return time.perf_counter()
    
    def end_system_timing(self, system_name: str, start_time: float) -> None:
        """End timing a system."""
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        if system_name not in self.system_timings:
            self.system_timings[system_name] = SystemTiming(name=system_name)
        
        self.system_timings[system_name].add_sample(elapsed_ms)
    
    def set_stat(self, name: str, value: Any) -> None:
        """Set a custom debug stat."""
        self.custom_stats[name] = value
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self._current_fps
    
    def get_avg_fps(self) -> float:
        """Get average FPS over sample window."""
        if self.fps_samples:
            return sum(self.fps_samples) / len(self.fps_samples)
        return 0.0
    
    def render(self, screen, font, x: int = 10, y: int = 10) -> None:
        """
        Render the debug overlay to screen.
        
        Args:
            screen: Pygame surface to render to
            font: Pygame font for text rendering
            x: X position for overlay
            y: Y position for overlay
        """
        if not self.enabled:
            return
        
        import pygame
        
        line_height = font.get_linesize() + 2
        current_y = y
        color = (0, 255, 0)  # Green text
        bg_color = (0, 0, 0, 180)  # Semi-transparent black
        
        lines = []
        
        # FPS
        lines.append(f"FPS: {self._current_fps:.1f} (avg: {self.get_avg_fps():.1f})")
        
        # System timings
        if self.system_timings:
            lines.append("--- Systems ---")
            for name, timing in sorted(self.system_timings.items(), 
                                       key=lambda x: x[1].avg_time_ms, reverse=True):
                lines.append(f"  {name}: {timing.avg_time_ms:.2f}ms (max: {timing.max_time_ms:.2f}ms)")
        
        # Custom stats
        if self.custom_stats:
            lines.append("--- Stats ---")
            for name, value in self.custom_stats.items():
                if isinstance(value, float):
                    lines.append(f"  {name}: {value:.2f}")
                else:
                    lines.append(f"  {name}: {value}")
        
        # Calculate background size
        max_width = max(font.size(line)[0] for line in lines) + 20
        total_height = len(lines) * line_height + 10
        
        # Draw background
        bg_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        bg_surface.fill(bg_color)
        screen.blit(bg_surface, (x - 5, y - 5))
        
        # Draw text
        for line in lines:
            text_surface = font.render(line, True, color)
            screen.blit(text_surface, (x, current_y))
            current_y += line_height
    
    def get_report(self) -> Dict[str, Any]:
        """Get a dictionary report of all debug data."""
        return {
            'fps': self._current_fps,
            'avg_fps': self.get_avg_fps(),
            'systems': {
                name: {
                    'avg_ms': timing.avg_time_ms,
                    'max_ms': timing.max_time_ms,
                    'last_ms': timing.last_time_ms
                }
                for name, timing in self.system_timings.items()
            },
            'stats': self.custom_stats.copy()
        }


class GameLogger:
    """
    Structured game event logger.
    
    Logs game events in JSON format for debugging and analytics.
    """
    
    def __init__(self, filepath: Optional[str] = None, max_entries: int = 10000):
        self.filepath = filepath
        self.entries: Deque[Dict[str, Any]] = deque(maxlen=max_entries)
        self._start_time = time.time()
    
    def log(self, event_type: str, **data) -> None:
        """
        Log a game event.
        
        Args:
            event_type: Type of event (message_sent, captured, delivered, etc.)
            **data: Event-specific data
        """
        entry = {
            'timestamp': time.time() - self._start_time,
            'type': event_type,
            **data
        }
        self.entries.append(entry)
    
    def log_message_sent(self, message_id: str, origin: str, dest: str, path: List[str]) -> None:
        """Log a message being sent."""
        self.log('message_sent', 
                 message_id=message_id, 
                 origin=origin, 
                 dest=dest, 
                 path=path)
    
    def log_message_delivered(self, message_id: str, dest: str, reward: int) -> None:
        """Log a message being delivered."""
        self.log('message_delivered',
                 message_id=message_id,
                 dest=dest,
                 reward=reward)
    
    def log_message_intercepted(self, message_id: str, interceptor: str, location: str) -> None:
        """Log a message being intercepted."""
        self.log('message_intercepted',
                 message_id=message_id,
                 interceptor=interceptor,
                 location=location)
    
    def log_bribe(self, target_id: str, cost: int, success: bool) -> None:
        """Log a bribe attempt."""
        self.log('bribe', target_id=target_id, cost=cost, success=success)
    
    def save(self) -> bool:
        """Save log entries to file."""
        if not self.filepath:
            return False
        
        try:
            import json
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(list(self.entries), f, indent=2)
            return True
        except Exception as e:
            print(f"Log save error: {e}")
            return False
    
    def get_entries(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get log entries, optionally filtered by type."""
        if event_type:
            return [e for e in self.entries if e.get('type') == event_type]
        return list(self.entries)


# Global debug instances
_debug_overlay: Optional[DebugOverlay] = None
_game_logger: Optional[GameLogger] = None


def get_debug_overlay() -> DebugOverlay:
    """Get or create the global debug overlay."""
    global _debug_overlay
    if _debug_overlay is None:
        _debug_overlay = DebugOverlay()
    return _debug_overlay


def get_game_logger(filepath: Optional[str] = None) -> GameLogger:
    """Get or create the global game logger."""
    global _game_logger
    if _game_logger is None:
        _game_logger = GameLogger(filepath)
    return _game_logger
