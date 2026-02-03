#!/usr/bin/env python3
"""
Modern Tetris - A polished Tetris clone with pygame-ce.

Features:
- Modern guideline Tetris rules
- SRS rotation system with wall kicks
- 7-bag randomizer
- Hold piece
- Ghost piece
- DAS/ARR input handling
- Particle effects
- Screen shake
- Multiple color palettes
- Deterministic replay system

Controls:
- Arrow keys: Move left/right, soft drop
- Up arrow: Rotate clockwise
- Z: Rotate counter-clockwise
- A: Rotate 180
- Space: Hard drop
- C: Hold piece
- R: Restart
- Escape: Pause

Author: Modern Tetris Project
"""

import sys
import time
from typing import Optional

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame
    except ImportError:
        print("Error: pygame-ce is required. Install with: pip install pygame-ce")
        sys.exit(1)

from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, WINDOW_TITLE,
    CELL_SIZE, DAS_DELAY, ARR_RATE, SOFT_DROP_RATE,
    LOCK_DELAY_FRAMES, MAX_LOCK_RESETS, GRAVITY_LEVELS,
    PALETTES, DEFAULT_PALETTE,
    MASTER_VOLUME, MUSIC_VOLUME, SFX_VOLUME
)

from src.engine.game_loop import GameLoop, GameState
from src.engine.config import Config
from src.tetris.game import TetrisGame, GameStatus
from src.input.input_handler import InputHandler, InputConfig
from src.render.renderer import Renderer
from src.audio.audio_manager import AudioManager, create_placeholder_sounds
from src.ui.menu import MainMenu, PauseMenu, GameOverMenu, SettingsMenu
from src.util.events import EventBus, GameEvent


class TetrisApp:
    """
    Main application class.
    
    Coordinates all game systems and manages the main loop.
    """
    
    def __init__(self):
        """Initialize the application."""
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Create window
        self._screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.DOUBLEBUF
        )
        
        # Initialize clock
        self._clock = pygame.time.Clock()
        
        # Load configuration
        self._config = Config()
        self._config.load()
        
        # Initialize audio
        self._audio = AudioManager(
            master_volume=MASTER_VOLUME,
            music_volume=MUSIC_VOLUME,
            sfx_volume=SFX_VOLUME
        )
        create_placeholder_sounds(self._audio)
        
        # Initialize renderer
        self._renderer = Renderer(
            self._screen,
            cell_size=CELL_SIZE,
            palette=PALETTES[DEFAULT_PALETTE]
        )
        
        # Initialize input
        self._input = InputHandler(InputConfig(
            das_delay=DAS_DELAY,
            arr_rate=ARR_RATE,
            soft_drop_rate=SOFT_DROP_RATE
        ))
        
        # Current palette
        self._current_palette = DEFAULT_PALETTE
        
        # Initialize menus
        self._main_menu = MainMenu(self._screen)
        self._pause_menu = PauseMenu(self._screen)
        self._game_over_menu = GameOverMenu(self._screen)
        self._settings_menu = SettingsMenu(self._screen)
        
        # Set up menu sound callbacks
        self._main_menu.set_sound_callback(self._audio.play_sound)
        self._pause_menu.set_sound_callback(self._audio.play_sound)
        self._game_over_menu.set_sound_callback(self._audio.play_sound)
        self._settings_menu.set_sound_callback(self._audio.play_sound)
        
        # Track where settings was opened from
        self._settings_return_state = GameState.MENU
        
        # Set up menu callbacks
        self._setup_menus()
        
        # Game state
        self._game: Optional[TetrisGame] = None
        self._state = GameState.MENU
        self._running = True
        self._in_settings = False
        
        # Event bus
        self._events = EventBus()
        self._setup_events()
    
    def _setup_menus(self) -> None:
        """Configure menu callbacks."""
        # Main menu
        self._main_menu.set_callbacks(
            on_start=self._start_game,
            on_settings=self._open_settings_from_menu,
            on_quit=self._quit
        )
        
        # Pause menu
        self._pause_menu.set_callbacks(
            on_resume=self._resume_game,
            on_restart=self._restart_game,
            on_settings=self._open_settings_from_pause,
            on_quit=self._quit_to_menu
        )
        
        # Game over menu
        self._game_over_menu.set_callbacks(
            on_restart=self._restart_game,
            on_quit=self._quit_to_menu
        )
        
        # Settings menu
        self._settings_menu.set_callbacks(
            on_back=self._close_settings,
            on_volume_change=self._on_volume_change,
            on_palette_change=self._on_palette_change
        )
        
        # Initialize settings values
        self._settings_menu.set_values(
            MASTER_VOLUME, SFX_VOLUME, MUSIC_VOLUME, self._current_palette
        )
    
    def _setup_events(self) -> None:
        """Set up event handlers."""
        self._events.subscribe(GameEvent.LINE_CLEAR, self._on_line_clear)
        self._events.subscribe(GameEvent.TSPIN, self._on_tspin)
        self._events.subscribe(GameEvent.PIECE_LOCK, self._on_piece_lock)
        self._events.subscribe(GameEvent.PIECE_HOLD, self._on_piece_hold)
        self._events.subscribe(GameEvent.PIECE_HARD_DROP, self._on_hard_drop)
        self._events.subscribe(GameEvent.LEVEL_UP, self._on_level_up)
        self._events.subscribe(GameEvent.GAME_OVER, self._on_game_over)
    
    def _start_game(self) -> None:
        """Start a new game."""
        seed = int(time.time() * 1000) % (2**31)
        
        self._game = TetrisGame(
            seed=seed,
            start_level=1,
            das_delay=DAS_DELAY,
            arr_rate=ARR_RATE,
            lock_delay=LOCK_DELAY_FRAMES,
            max_lock_resets=MAX_LOCK_RESETS,
            gravity_table=GRAVITY_LEVELS
        )
        
        # Set up game callbacks
        self._game.on_line_clear(lambda n, rows: self._events.emit(
            GameEvent.LINE_CLEAR, {"lines": n, "rows": rows}
        ))
        self._game.on_tspin(lambda t, n: self._events.emit(
            GameEvent.TSPIN, {"type": t, "lines": n}
        ))
        self._game.on_piece_lock(lambda p: self._events.emit(
            GameEvent.PIECE_LOCK, {"piece": p}
        ))
        self._game.on_piece_hold(lambda p: self._events.emit(
            GameEvent.PIECE_HOLD, {"piece": p}
        ))
        self._game.on_hard_drop(lambda d: self._events.emit(
            GameEvent.PIECE_HARD_DROP, {"distance": d}
        ))
        self._game.on_level_up(lambda l: self._events.emit(
            GameEvent.LEVEL_UP, {"level": l}
        ))
        self._game.on_game_over(lambda: self._events.emit(GameEvent.GAME_OVER))
        
        # Bind input actions
        self._input.bind_action("move_left", self._game.move_left)
        self._input.bind_action("move_right", self._game.move_right)
        self._input.bind_action("soft_drop", self._game.soft_drop)
        self._input.bind_action("hard_drop", self._game.hard_drop)
        self._input.bind_action("rotate_cw", self._game.rotate_cw)
        self._input.bind_action("rotate_ccw", self._game.rotate_ccw)
        self._input.bind_action("rotate_180", self._game.rotate_180)
        self._input.bind_action("hold", self._game.hold)
        
        self._state = GameState.PLAYING
        self._audio.play_sound("menu_select")
    
    def _resume_game(self) -> None:
        """Resume paused game."""
        if self._game:
            self._game.resume()
        self._state = GameState.PLAYING
    
    def _restart_game(self) -> None:
        """Restart the game."""
        self._start_game()
    
    def _pause_game(self) -> None:
        """Pause the game."""
        if self._game:
            self._game.pause()
        self._state = GameState.PAUSED
    
    def _quit_to_menu(self) -> None:
        """Return to main menu."""
        self._game = None
        self._state = GameState.MENU
        self._input.reset()
    
    def _open_settings_from_menu(self) -> None:
        """Open settings from main menu."""
        self._settings_return_state = GameState.MENU
        self._open_settings()
    
    def _open_settings_from_pause(self) -> None:
        """Open settings from pause menu."""
        self._settings_return_state = GameState.PAUSED
        self._open_settings()
    
    def _open_settings(self) -> None:
        """Open settings menu using _in_settings flag overlay."""
        self._in_settings = True
        self._audio.play_sound("menu_select")
    
    def _close_settings(self) -> None:
        """Close settings and return to previous state."""
        self._in_settings = False
        self._state = self._settings_return_state
        self._audio.play_sound("menu_select")
    
    def _on_volume_change(self, volume_type: str, value: float) -> None:
        """Handle volume change from settings."""
        if volume_type == "master":
            self._audio.set_master_volume(value)
        elif volume_type == "sfx":
            self._audio.set_sfx_volume(value)
        elif volume_type == "music":
            self._audio.set_music_volume(value)
    
    def _on_palette_change(self, palette: str) -> None:
        """Handle palette change from settings."""
        self._current_palette = palette
        if palette in PALETTES:
            self._renderer.set_palette(PALETTES[palette])
            self._audio.play_sound("menu_select")
    
    def _quit(self) -> None:
        """Quit the application."""
        self._running = False
    
    # Event handlers
    def _on_line_clear(self, event) -> None:
        lines = event.data.get("lines", 0)
        rows = event.data.get("rows", [])
        
        self._audio.play_line_clear(lines)
        self._renderer.trigger_line_clear(lines, rows)
    
    def _on_tspin(self, event) -> None:
        tspin_type = event.data.get("type", "none")
        
        self._audio.play_tspin()
        
        if self._game and self._game.current_piece:
            piece = self._game.current_piece
            self._renderer.trigger_tspin(
                piece.x + 1, 
                piece.y + 1,
                is_mini=(tspin_type == "mini")
            )
    
    def _on_piece_lock(self, event) -> None:
        self._audio.play_lock()
    
    def _on_piece_hold(self, event) -> None:
        self._audio.play_hold()
    
    def _on_hard_drop(self, event) -> None:
        self._audio.play_hard_drop()
        
        if self._game and self._game.current_piece:
            piece = self._game.current_piece
            self._renderer.trigger_hard_drop(piece.x, piece.y, piece)
    
    def _on_level_up(self, event) -> None:
        self._audio.play_level_up()
    
    def _on_game_over(self, event=None) -> None:
        self._audio.play_game_over()
        
        if self._game:
            self._game_over_menu.set_final_stats(
                self._game.score,
                self._game.lines,
                self._game.level
            )
        
        self._state = GameState.GAME_OVER
    
    def _handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events."""
        if event.type == pygame.QUIT:
            self._running = False
            return
        
        # Handle settings menu first if open
        if self._in_settings:
            self._settings_menu.handle_event(event)
            return
        
        if self._state == GameState.MENU:
            self._main_menu.handle_event(event)
        
        elif self._state == GameState.PLAYING:
            self._input.handle_event(event)
            
            # Check for pause
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._pause_game()
                elif event.key == pygame.K_r:
                    self._restart_game()
        
        elif self._state == GameState.PAUSED:
            self._pause_menu.handle_event(event)
        
        elif self._state == GameState.GAME_OVER:
            self._game_over_menu.handle_event(event)
    
    def _update(self, dt: float) -> None:
        """Update game logic."""
        # Update settings menu if open
        if self._in_settings:
            self._settings_menu.update(dt)
            return
        
        if self._state == GameState.PLAYING and self._game:
            # Update input
            self._input.update()
            
            # Update game
            self._game.update()
            
            # Check for game over
            if self._game.status == GameStatus.GAME_OVER:
                self._on_game_over()
        
        elif self._state == GameState.MENU:
            self._main_menu.update(dt)
        
        elif self._state == GameState.PAUSED:
            self._pause_menu.update(dt)
        
        elif self._state == GameState.GAME_OVER:
            self._game_over_menu.update(dt)
        
        # Update renderer (particles, etc.)
        self._renderer.update(dt)
    
    def _render(self) -> None:
        """Render the game."""
        # Render settings if open
        if self._in_settings:
            # Draw background based on return state
            if self._settings_return_state == GameState.PAUSED and self._game:
                self._renderer.render(self._game)
                # Darken
                overlay = pygame.Surface((self._screen.get_width(), self._screen.get_height()), pygame.SRCALPHA)
                overlay.fill((10, 10, 20, 200))
                self._screen.blit(overlay, (0, 0))
            else:
                pass  # Settings menu draws its own background
            self._settings_menu.draw()
            return
        
        if self._state == GameState.MENU:
            self._main_menu.draw()
        
        elif self._state == GameState.PLAYING and self._game:
            self._renderer.render(self._game)
        
        elif self._state == GameState.PAUSED and self._game:
            # Draw game in background
            self._renderer.render(self._game)
            # Draw pause menu on top
            self._pause_menu.draw()
        
        elif self._state == GameState.GAME_OVER and self._game:
            # Draw game in background
            self._renderer.render(self._game)
            # Draw game over menu on top
            self._game_over_menu.draw()
    
    def run(self) -> None:
        """Run the main game loop."""
        last_time = time.perf_counter()
        
        while self._running:
            # Calculate delta time
            current_time = time.perf_counter()
            dt = current_time - last_time
            last_time = current_time
            
            # Cap delta time
            if dt > 0.25:
                dt = 0.25
            
            # Handle events
            for event in pygame.event.get():
                self._handle_event(event)
            
            # Update
            self._update(dt)
            
            # Render
            self._render()
            
            # Flip display
            pygame.display.flip()
            
            # Cap frame rate
            self._clock.tick(FPS)
        
        # Cleanup
        pygame.quit()


def main():
    """Entry point."""
    app = TetrisApp()
    app.run()


if __name__ == "__main__":
    main()
