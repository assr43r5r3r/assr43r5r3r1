"""
Main game loop with fixed timestep logic updates.
"""

import time
from typing import Callable, Optional
from enum import Enum, auto

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


class GameState(Enum):
    """Game state machine states."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class GameLoop:
    """
    Fixed timestep game loop.
    
    Logic updates run at a fixed rate (60 FPS) for deterministic behavior.
    Rendering runs as fast as possible with interpolation.
    """
    
    TARGET_FPS = 60
    FIXED_DT = 1.0 / TARGET_FPS
    MAX_FRAME_TIME = 0.25  # Prevent spiral of death
    
    def __init__(self):
        self._running = False
        self._accumulator = 0.0
        self._current_time = 0.0
        self._frame_count = 0
        self._logic_frame = 0
        
        # Callbacks
        self._update_fn: Optional[Callable[[float], None]] = None
        self._render_fn: Optional[Callable[[float], None]] = None
        self._event_fn: Optional[Callable[[pygame.event.Event], None]] = None
        
        # State
        self._state = GameState.MENU
        self._paused = False
        
        # Performance tracking
        self._fps = 0.0
        self._fps_timer = 0.0
        self._fps_count = 0
    
    def set_callbacks(
        self,
        update: Callable[[float], None],
        render: Callable[[float], None],
        event_handler: Callable[[pygame.event.Event], None]
    ) -> None:
        """
        Set the game loop callbacks.
        
        Args:
            update: Logic update function, receives delta time
            render: Render function, receives interpolation alpha
            event_handler: Event handler function
        """
        self._update_fn = update
        self._render_fn = render
        self._event_fn = event_handler
    
    def run(self) -> None:
        """
        Start the game loop.
        Runs until stop() is called.
        """
        if not all([self._update_fn, self._render_fn, self._event_fn]):
            raise RuntimeError("Must set all callbacks before running")
        
        self._running = True
        self._current_time = time.perf_counter()
        
        while self._running:
            # Calculate frame time
            new_time = time.perf_counter()
            frame_time = new_time - self._current_time
            self._current_time = new_time
            
            # Clamp frame time to prevent spiral of death
            if frame_time > self.MAX_FRAME_TIME:
                frame_time = self.MAX_FRAME_TIME
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                else:
                    self._event_fn(event)
            
            # Fixed timestep logic updates
            if not self._paused:
                self._accumulator += frame_time
                
                while self._accumulator >= self.FIXED_DT:
                    self._update_fn(self.FIXED_DT)
                    self._accumulator -= self.FIXED_DT
                    self._logic_frame += 1
            
            # Render with interpolation
            alpha = self._accumulator / self.FIXED_DT
            self._render_fn(alpha)
            
            pygame.display.flip()
            self._frame_count += 1
            
            # FPS calculation
            self._fps_count += 1
            self._fps_timer += frame_time
            if self._fps_timer >= 1.0:
                self._fps = self._fps_count / self._fps_timer
                self._fps_count = 0
                self._fps_timer = 0.0
    
    def stop(self) -> None:
        """Stop the game loop."""
        self._running = False
    
    def pause(self) -> None:
        """Pause logic updates."""
        self._paused = True
    
    def resume(self) -> None:
        """Resume logic updates."""
        self._paused = False
    
    @property
    def is_running(self) -> bool:
        """Check if game loop is running."""
        return self._running
    
    @property
    def is_paused(self) -> bool:
        """Check if game is paused."""
        return self._paused
    
    @property
    def fps(self) -> float:
        """Get current FPS."""
        return self._fps
    
    @property
    def logic_frame(self) -> int:
        """Get current logic frame number."""
        return self._logic_frame
    
    @property
    def state(self) -> GameState:
        """Get current game state."""
        return self._state
    
    @state.setter
    def state(self, value: GameState) -> None:
        """Set game state."""
        self._state = value
        if value == GameState.PAUSED:
            self.pause()
        elif value == GameState.PLAYING:
            self.resume()
