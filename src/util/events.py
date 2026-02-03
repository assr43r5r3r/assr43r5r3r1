"""
Event system for decoupling game logic from rendering and audio.
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field


class GameEvent(Enum):
    """All game events that can be emitted."""
    # Piece events
    PIECE_SPAWN = auto()
    PIECE_MOVE = auto()
    PIECE_ROTATE = auto()
    PIECE_LOCK = auto()
    PIECE_HOLD = auto()
    PIECE_HARD_DROP = auto()
    
    # Line clear events
    LINE_CLEAR = auto()
    TETRIS = auto()
    TSPIN = auto()
    TSPIN_MINI = auto()
    PERFECT_CLEAR = auto()
    
    # Combo/bonus events
    COMBO = auto()
    BACK_TO_BACK = auto()
    
    # Game state events
    GAME_START = auto()
    GAME_OVER = auto()
    GAME_PAUSE = auto()
    GAME_RESUME = auto()
    LEVEL_UP = auto()
    
    # UI events
    MENU_SELECT = auto()
    MENU_BACK = auto()


@dataclass
class EventData:
    """Data associated with an event."""
    event: GameEvent
    data: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """
    Central event bus for game events.
    Allows systems to subscribe to and emit events without direct coupling.
    """
    
    def __init__(self):
        self._listeners: Dict[GameEvent, List[Callable[[EventData], None]]] = {}
        self._pending_events: List[EventData] = []
    
    def subscribe(self, event: GameEvent, callback: Callable[[EventData], None]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event: The event type to subscribe to
            callback: Function to call when event is emitted
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def unsubscribe(self, event: GameEvent, callback: Callable[[EventData], None]) -> None:
        """
        Unsubscribe from an event type.
        """
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)
    
    def emit(self, event: GameEvent, data: Dict[str, Any] = None) -> None:
        """
        Emit an event immediately.
        
        Args:
            event: The event type to emit
            data: Optional data to pass with the event
        """
        event_data = EventData(event, data or {})
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(event_data)
    
    def queue(self, event: GameEvent, data: Dict[str, Any] = None) -> None:
        """
        Queue an event to be processed later.
        """
        self._pending_events.append(EventData(event, data or {}))
    
    def process_queue(self) -> None:
        """
        Process all queued events.
        """
        events = self._pending_events.copy()
        self._pending_events.clear()
        
        for event_data in events:
            if event_data.event in self._listeners:
                for callback in self._listeners[event_data.event]:
                    callback(event_data)
    
    def clear(self) -> None:
        """Clear all listeners and queued events."""
        self._listeners.clear()
        self._pending_events.clear()
