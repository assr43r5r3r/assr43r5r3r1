"""
Application shell and state manager for Signal to Noise.

Manages game states, fixed-timestep game loop, and main rendering.
"""

import pygame
from typing import Dict, Optional, Type
from .settings import get_settings, apply_low_end_mode
from .states.base_state import BaseState
from .states.menu_state import MenuState
from .states.game_state import GameState
from .states.routing_state import RoutingState
from .states.event_state import EventState
from .utils.debug import get_debug_overlay


class App:
    """
    Main application class.
    
    Manages:
    - Pygame initialization
    - Game states and transitions
    - Fixed-timestep game loop
    - Global resources
    """
    
    def __init__(self, low_end: bool = False):
        """
        Initialize the application.
        
        Args:
            low_end: Enable low-end mode for better performance
        """
        self.settings = get_settings()
        
        if low_end:
            apply_low_end_mode()
        
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        
        # Set up display
        flags = pygame.DOUBLEBUF
        if self.settings.FULLSCREEN:
            flags |= pygame.FULLSCREEN
        
        self.screen = pygame.display.set_mode(
            (self.settings.SCREEN_WIDTH, self.settings.SCREEN_HEIGHT),
            flags
        )
        pygame.display.set_caption("Signal to Noise")
        
        # Clock for timing
        self.clock = pygame.time.Clock()
        
        # State management
        self.states: Dict[str, Type[BaseState]] = {}
        self.current_state: Optional[BaseState] = None
        self.state_name: str = ""
        
        # Running flag
        self.running = True
        
        # Fixed timestep
        self.logic_dt = 1.0 / self.settings.LOGIC_TICK_RATE
        self.accumulator = 0.0
        
        # Debug overlay
        self.debug_overlay = get_debug_overlay()
        
        # Register states
        self._register_states()
    
    def _register_states(self) -> None:
        """Register all game states."""
        self.states = {
            'menu': MenuState,
            'game': GameState,
            'routing': RoutingState,
            'event': EventState,
        }
    
    def start(self, initial_state: str = 'menu') -> None:
        """
        Start the application.
        
        Args:
            initial_state: Name of the initial state to enter
        """
        self._change_state(initial_state, {})
        self._main_loop()
    
    def _change_state(self, state_name: str, persistent: dict) -> None:
        """
        Change to a new state.
        
        Args:
            state_name: Name of the state to change to
            persistent: Data to pass to the new state
        """
        if state_name not in self.states:
            print(f"Unknown state: {state_name}")
            return
        
        # Cleanup current state
        if self.current_state:
            persistent = self.current_state.cleanup()
        
        # Create and start new state
        self.state_name = state_name
        self.current_state = self.states[state_name](self)
        self.current_state.startup(persistent)
    
    def _main_loop(self) -> None:
        """Main game loop with fixed timestep."""
        while self.running:
            # Get frame time
            frame_dt = self.clock.tick(self.settings.FPS_CAP) / 1000.0
            
            # Cap frame time to prevent spiral of death
            frame_dt = min(frame_dt, 0.1)
            
            # Handle events
            self._handle_events()
            
            # Fixed timestep update
            self.accumulator += frame_dt
            
            while self.accumulator >= self.logic_dt:
                self._update(self.logic_dt)
                self.accumulator -= self.logic_dt
            
            # Render at variable rate
            self._render()
            
            # Check for state change
            if self.current_state and self.current_state.done:
                self._change_state(
                    self.current_state.next_state,
                    self.current_state.cleanup()
                )
            
            pygame.display.flip()
        
        self._cleanup()
    
    def _handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                if self.current_state:
                    self.current_state.handle_event(event)
    
    def _update(self, dt: float) -> None:
        """Update current state."""
        if self.current_state:
            self.current_state.update(dt)
    
    def _render(self) -> None:
        """Render current state."""
        if self.current_state:
            self.current_state.render(self.screen)
    
    def _cleanup(self) -> None:
        """Cleanup before exit."""
        pygame.quit()
    
    def quit(self) -> None:
        """Request application quit."""
        self.running = False
