"""
Base State class for game state management.

All game states inherit from this class.
"""

from typing import Optional, Any, TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from ..app import App


class BaseState:
    """
    Base class for all game states.
    
    States handle specific game modes (menu, gameplay, routing, etc.)
    and are managed by the App state machine.
    """
    
    def __init__(self, app: 'App'):
        """
        Initialize the state.
        
        Args:
            app: Reference to the main App instance
        """
        self.app = app
        self.next_state: Optional[str] = None
        self.done: bool = False
        self.persist: dict = {}
    
    def startup(self, persistent: dict) -> None:
        """
        Called when state becomes active.
        
        Args:
            persistent: Data passed from previous state
        """
        self.persist = persistent
        self.done = False
        self.next_state = None
    
    def cleanup(self) -> dict:
        """
        Called when state is about to become inactive.
        
        Returns:
            Data to pass to next state
        """
        return self.persist
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle a pygame event.
        
        Args:
            event: Pygame event to handle
        """
        pass
    
    def update(self, dt: float) -> None:
        """
        Update state logic.
        
        Args:
            dt: Delta time since last update in seconds
        """
        pass
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the state.
        
        Args:
            screen: Pygame surface to render to
        """
        pass
    
    def change_state(self, state_name: str, **kwargs) -> None:
        """
        Request a state change.
        
        Args:
            state_name: Name of state to change to
            **kwargs: Data to pass to new state
        """
        self.next_state = state_name
        self.persist.update(kwargs)
        self.done = True
