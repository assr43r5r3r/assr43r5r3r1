"""
Input buffering for responsive controls.
"""

from typing import Set, Optional
from dataclasses import dataclass, field
from enum import Enum, auto


class InputState(Enum):
    """Input key states."""
    RELEASED = auto()
    PRESSED = auto()
    HELD = auto()


@dataclass
class BufferedInput:
    """A buffered input action with timing info."""
    action: str
    frames_remaining: int
    
    def tick(self) -> bool:
        """
        Decrement buffer timer.
        
        Returns:
            True if buffer expired
        """
        self.frames_remaining -= 1
        return self.frames_remaining <= 0


class InputBuffer:
    """
    Input buffering system for responsive controls.
    
    Buffers inputs for a short time to allow for imprecise timing.
    """
    
    DEFAULT_BUFFER_FRAMES = 6  # ~100ms at 60 FPS
    
    def __init__(self, buffer_frames: int = None):
        """
        Initialize input buffer.
        
        Args:
            buffer_frames: Number of frames to buffer inputs
        """
        self._buffer_frames = buffer_frames or self.DEFAULT_BUFFER_FRAMES
        self._buffered_inputs: dict[str, BufferedInput] = {}
        self._consumed: Set[str] = set()
    
    def buffer(self, action: str) -> None:
        """
        Add an action to the buffer.
        
        Args:
            action: The action to buffer
        """
        self._buffered_inputs[action] = BufferedInput(
            action=action,
            frames_remaining=self._buffer_frames
        )
    
    def consume(self, action: str) -> bool:
        """
        Try to consume a buffered action.
        
        Args:
            action: The action to consume
        
        Returns:
            True if action was buffered and consumed
        """
        if action in self._buffered_inputs and action not in self._consumed:
            self._consumed.add(action)
            return True
        return False
    
    def is_buffered(self, action: str) -> bool:
        """Check if an action is currently buffered."""
        return action in self._buffered_inputs and action not in self._consumed
    
    def update(self) -> None:
        """Update buffer timers (call once per frame)."""
        expired = []
        
        for action, buffered in self._buffered_inputs.items():
            if buffered.tick():
                expired.append(action)
        
        for action in expired:
            del self._buffered_inputs[action]
            self._consumed.discard(action)
    
    def clear(self) -> None:
        """Clear all buffered inputs."""
        self._buffered_inputs.clear()
        self._consumed.clear()


@dataclass
class DASState:
    """State for Delayed Auto Shift."""
    delay: int  # Frames before auto-repeat starts
    rate: int   # Frames between repeats
    
    counter: int = 0
    is_active: bool = False
    direction: int = 0  # -1 = left, 1 = right
    
    def reset(self) -> None:
        """Reset DAS state."""
        self.counter = 0
        self.is_active = False
        self.direction = 0
    
    def start(self, direction: int) -> None:
        """Start DAS in a direction."""
        if self.direction != direction:
            self.counter = 0
        self.direction = direction
        self.is_active = True
    
    def stop(self) -> None:
        """Stop DAS."""
        self.is_active = False
        self.direction = 0
        self.counter = 0
    
    def update(self) -> bool:
        """
        Update DAS counter.
        
        Returns:
            True if should trigger movement
        """
        if not self.is_active:
            return False
        
        self.counter += 1
        
        # Initial delay
        if self.counter == self.delay:
            return True
        
        # Auto repeat
        if self.counter > self.delay:
            if self.rate == 0:
                return True  # Instant repeat
            if (self.counter - self.delay) % self.rate == 0:
                return True
        
        return False
