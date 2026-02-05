#!/usr/bin/env python3
"""
BlockFall - A Modern Puzzle Experience

A polished Tetris clone with pygame-ce featuring modern aesthetics.

Features:
- 25-stage system with increasing difficulty
- Player profiles and leaderboard
- Save/load system
- Modern UI with smooth animations
- Multiple visual themes
- Loading screen and polished transitions

Controls:
- Arrow keys or WASD: Move left/right, soft drop
- Up arrow or W: Rotate clockwise
- Z: Rotate counter-clockwise
- Space: Hard drop
- C: Hold piece
- Escape: Pause/Exit

Author: BlockFall Project
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
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, GAME_NAME,
    CELL_SIZE, DAS_DELAY, ARR_RATE, SOFT_DROP_RATE,
    LOCK_DELAY_FRAMES, MAX_LOCK_RESETS,
    PALETTES, DEFAULT_PALETTE,
    MASTER_VOLUME, MUSIC_VOLUME, SFX_VOLUME,
    SCORE_PER_ROW, SAVE_DIRECTORY, NEXT_PIECES_PREVIEW,
    AVATAR_SIZE_GAMEPLAY
)

from src.engine.game_loop import GameLoop, GameState
from src.engine.config import Config
from src.tetris.game import TetrisGame, GameStatus
from src.tetris.stages import StageManager, STAGES
from src.input.input_handler import InputHandler, InputConfig
from src.render.renderer import Renderer
from src.audio.audio_manager import AudioManager, create_placeholder_sounds
from src.ui.menu import MainMenu, PauseMenu, GameOverMenu, SettingsMenu
from src.ui.overlays import Countdown, StageTransition, ConfirmDialog
from src.ui.screens import NameEntryScreen, LeaderboardScreen
from src.ui.loading import LoadingScreen
from src.save.save_manager import SaveManager
from src.util.events import EventBus, GameEvent
from src.story.story_presentation import StoryPresentation, DialogueMessage
from src.story.story_manager import StoryManager, DialogueLine, CHARACTERS


# Frame rate constants for adaptive FPS
FPS_GAMEPLAY = 60  # Full 60 FPS during gameplay
FPS_MENU = 30      # 30 FPS for menus (sufficient for UI)

# UI Constants
DRAG_ZONE_HEIGHT = 40  # Height of draggable area at top of window
ACCENT_COLOR_BLUE = (100, 180, 255)  # Modern blue accent color


class TetrisApp:
    """
    Main application class.
    
    Coordinates all game systems and manages the main loop.
    """
    
    def __init__(self):
        """Initialize the application."""
        # Initialize pygame
        pygame.init()
        
        # Create borderless window (no title bar)
        self._screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.DOUBLEBUF | pygame.NOFRAME
        )
        
        # Hide the default pygame icon (set a blank icon)
        blank_icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        blank_icon.fill((0, 0, 0, 0))
        pygame.display.set_icon(blank_icon)
        
        # Initialize clock
        self._clock = pygame.time.Clock()
        
        # Load configuration
        self._config = Config()
        self._config.load()
        
        # Initialize save manager
        self._save_manager = SaveManager(SAVE_DIRECTORY)
        
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
        
        # Stage manager
        self._stage_manager = StageManager()
        
        # Game timer
        self._game_timer = 0.0  # Time in seconds
        
        # Initialize menus
        self._main_menu = MainMenu(self._screen)
        self._pause_menu = PauseMenu(self._screen)
        self._game_over_menu = GameOverMenu(self._screen)
        self._settings_menu = SettingsMenu(self._screen)
        
        # Initialize loading screen
        self._loading_screen = LoadingScreen(self._screen, GAME_NAME)
        self._loading_screen.set_on_complete(self._on_loading_complete)
        self._in_loading = True
        
        # Initialize overlays
        self._countdown = Countdown(self._screen)
        self._stage_transition = StageTransition(self._screen)
        self._confirm_dialog = ConfirmDialog(self._screen)
        
        # Initialize screens
        self._name_entry = NameEntryScreen(self._screen)
        self._leaderboard_screen = LeaderboardScreen(self._screen)
        
        # Initialize story mode presentation
        self._story_manager = StoryManager()
        self._story_presentation = StoryPresentation(self._screen)
        self._story_presentation.set_sound_callback(self._audio.play_sound)
        self._in_story_mode = False
        self._in_story_dialogue = False
        
        # Set up sound callbacks
        for component in [
            self._main_menu, self._pause_menu, self._game_over_menu,
            self._settings_menu, self._countdown, self._stage_transition,
            self._confirm_dialog, self._name_entry, self._leaderboard_screen
        ]:
            component.set_sound_callback(self._audio.play_sound)
        
        # Track where settings was opened from
        self._settings_return_state = GameState.MENU
        
        # Set up menu callbacks
        self._setup_menus()
        
        # Game state
        self._game: Optional[TetrisGame] = None
        self._state = GameState.MENU
        self._running = True
        self._in_settings = False
        self._in_countdown = False
        self._waiting_for_profile = False
        
        # Window dragging support - check if API is available
        self._dragging_window = False
        self._drag_offset = (0, 0)
        self._window_dragging_supported = (
            hasattr(pygame.display, 'get_window_position') and 
            hasattr(pygame.display, 'set_window_position')
        )
        
        # Menu button rect for gameplay (initialized in draw)
        self._menu_button_rect = pygame.Rect(0, 0, 0, 0)
        
        # Back button rect (top-left corner)
        self._back_button_rect = pygame.Rect(20, 20, 40, 40)
        
        # Add leaderboard button to main menu
        self._setup_main_menu_extras()
        
        # Event bus
        self._events = EventBus()
        self._setup_events()
        
        # Surface caching for performance optimization
        self._cached_surfaces: dict = {}
        self._cache_dirty = True
        
        # Current target FPS (adaptive)
        self._current_fps = FPS_MENU
        
        # Update main menu with player info
        self._update_main_menu_player()
    
    def _on_loading_complete(self) -> None:
        """Called when loading screen finishes."""
        self._in_loading = False
        # Don't show name entry on launch - will show when player clicks Play without a profile
    
    def _update_main_menu_player(self) -> None:
        """Update main menu with current player info."""
        player = self._save_manager.current_player
        if player:
            avatar = player.get_avatar_surface()
            self._main_menu.set_player_info(player.name, avatar)
        else:
            self._main_menu.set_player_info("Guest", None)
    
    def _setup_main_menu_extras(self) -> None:
        """Add extra buttons to main menu."""
        # The main menu already has Play, Settings, Quit
        # We'll modify it to include Leaderboard
        pass  # Handled in menu setup
    
    def _setup_menus(self) -> None:
        """Configure menu callbacks."""
        # Main menu - updated for modern style with leaderboard icon
        self._main_menu.set_callbacks(
            on_regular=self._request_regular_game,
            on_story=self._request_story_mode,
            on_leaderboard=self._show_leaderboard,
            on_settings=self._open_settings_from_menu,
            on_quit=self._request_quit,
            on_switch_player=self._show_switch_player
        )
        
        # Pause menu
        self._pause_menu.set_callbacks(
            on_resume=self._resume_game,
            on_restart=self._request_restart,
            on_settings=self._open_settings_from_pause,
            on_quit=self._request_quit_to_menu
        )
        
        # Game over menu
        self._game_over_menu.set_callbacks(
            on_restart=self._request_regular_game,
            on_quit=self._quit_to_menu
        )
        
        # Settings menu - with additional callbacks for leaderboard and add player
        self._settings_menu.set_callbacks(
            on_back=self._close_settings,
            on_volume_change=self._on_volume_change,
            on_palette_change=self._on_palette_change,
            on_toggle_ghost=self._on_toggle_ghost,
            on_toggle_particles=self._on_toggle_particles,
            on_toggle_shake=self._on_toggle_shake,
            on_leaderboard=self._show_leaderboard,
            on_add_player=self._show_add_player
        )
        
        # Countdown
        self._countdown.set_on_complete(self._on_countdown_complete)
        
        # Stage transition
        self._stage_transition.set_on_complete(self._on_stage_transition_complete)
        
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
        self._events.subscribe(GameEvent.LEVEL_UP, self._on_stage_change)
        self._events.subscribe(GameEvent.GAME_OVER, self._on_game_over)
    
    def _on_profile_created(self, name: str, avatar_path: Optional[str]) -> None:
        """Handle profile creation."""
        profile = self._save_manager.profiles.create_profile(name, avatar_path)
        self._save_manager.profiles.set_current_profile(profile.id)
        self._waiting_for_profile = False
        self._update_main_menu_player()
    
    def _request_regular_game(self) -> None:
        """Request to start a regular game."""
        if not self._save_manager.current_player:
            self._waiting_for_profile = True
            self._name_entry.show(
                on_confirm=self._on_profile_created_and_start,
                on_cancel=lambda: setattr(self, '_waiting_for_profile', False)
            )
        else:
            self._start_countdown()
    
    def _request_story_mode(self) -> None:
        """Request to start story mode with graphic novel presentation."""
        if not self._save_manager.current_player:
            self._waiting_for_profile = True
            self._name_entry.show(
                on_confirm=self._on_profile_created_and_start_story,
                on_cancel=lambda: setattr(self, '_waiting_for_profile', False)
            )
        else:
            self._start_story_chapter(1)
    
    def _on_profile_created_and_start_story(self, name: str, avatar_path: Optional[str]) -> None:
        """Handle profile creation and start story mode."""
        self._on_profile_created(name, avatar_path)
        self._start_story_chapter(1)
    
    def _start_story_chapter(self, chapter_id: int) -> None:
        """Start a story mode chapter."""
        chapter = self._story_manager.start_chapter(chapter_id)
        if not chapter:
            self._confirm_dialog.show(
                "Story Mode",
                "Chapter not found or not available yet.",
                on_confirm=lambda: None,
                on_cancel=lambda: None
            )
            return
        
        self._in_story_mode = True
        
        # Start intro dialogue if available
        if chapter.intro_dialogue:
            self._in_story_dialogue = True
            dialogue_messages = [
                DialogueMessage(line.character_id, line.text, line.emotion)
                for line in chapter.intro_dialogue
            ]
            self._story_presentation.start_dialogue(
                dialogue_messages,
                on_complete=self._on_story_dialogue_complete
            )
        else:
            self._start_countdown()
        
        self._audio.play_sound("menu_select")
    
    def _on_story_dialogue_complete(self) -> None:
        """Called when story dialogue finishes."""
        self._in_story_dialogue = False
        self._start_countdown()
    
    def _show_leaderboard(self) -> None:
        """Show the leaderboard screen."""
        entries = self._save_manager.leaderboard.get_top(20)
        self._leaderboard_screen.show(entries, on_close=lambda: None)
    
    def _show_add_player(self) -> None:
        """Show the add player screen."""
        self._waiting_for_profile = True
        self._name_entry.show(
            on_confirm=self._on_profile_created,
            on_cancel=lambda: setattr(self, '_waiting_for_profile', False)
        )
    
    def _show_switch_player(self) -> None:
        """Show player switch/selection dialog."""
        profiles = self._save_manager.profiles.get_all_profiles()
        if len(profiles) <= 1:
            # No other players, show add player instead
            self._show_add_player()
        else:
            # For now, cycle to next player
            current = self._save_manager.current_player
            current_idx = 0
            for i, p in enumerate(profiles):
                if current and p.id == current.id:
                    current_idx = i
                    break
            next_idx = (current_idx + 1) % len(profiles)
            self._save_manager.profiles.set_current_profile(profiles[next_idx].id)
            self._update_main_menu_player()
            self._audio.play_sound("menu_select")
    
    def _on_profile_created_and_start(self, name: str, avatar_path: Optional[str]) -> None:
        """Handle profile creation and start game."""
        self._on_profile_created(name, avatar_path)
        self._start_countdown()
    
    def _start_countdown(self) -> None:
        """Start the countdown animation."""
        self._in_countdown = True
        self._countdown.start()
        self._state = GameState.PLAYING  # Switch to playing state for rendering
    
    def _on_countdown_complete(self) -> None:
        """Called when countdown finishes."""
        self._in_countdown = False
        self._start_game()
    
    def _start_game(self) -> None:
        """Start a new game."""
        seed = int(time.time() * 1000) % (2**31)
        
        # Reset stage manager
        self._stage_manager.reset()
        
        # Get gravity from stage system
        initial_gravity = self._stage_manager.get_gravity()
        gravity_table = {i: STAGES[i + 1].gravity_frames for i in range(25)}
        
        self._game = TetrisGame(
            seed=seed,
            start_level=1,
            das_delay=DAS_DELAY,
            arr_rate=ARR_RATE,
            lock_delay=LOCK_DELAY_FRAMES,
            max_lock_resets=MAX_LOCK_RESETS,
            gravity_table=gravity_table
        )
        
        # Reset game timer
        self._game_timer = 0.0
        
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
        
        # Bind input actions (no rotate_180)
        self._input.bind_action("move_left", self._game.move_left)
        self._input.bind_action("move_right", self._game.move_right)
        self._input.bind_action("soft_drop", self._game.soft_drop)
        self._input.bind_action("hard_drop", self._game.hard_drop)
        self._input.bind_action("rotate_cw", self._game.rotate_cw)
        self._input.bind_action("rotate_ccw", self._game.rotate_ccw)
        self._input.bind_action("hold", self._game.hold)
        
        self._state = GameState.PLAYING
        self._audio.play_sound("menu_select")
    
    def _resume_game(self) -> None:
        """Resume paused game."""
        if self._game:
            self._game.resume()
        self._state = GameState.PLAYING
    
    def _request_restart(self) -> None:
        """Request restart - shows confirmation if in game."""
        self._confirm_dialog.show(
            "Restart Game?",
            "Your progress will be lost.",
            on_confirm=self._restart_game,
            on_cancel=lambda: None
        )
    
    def _restart_game(self) -> None:
        """Restart the game."""
        self._start_countdown()
    
    def _pause_game(self) -> None:
        """Pause the game."""
        if self._game:
            self._game.pause()
        self._state = GameState.PAUSED
    
    def _request_quit_to_menu(self) -> None:
        """Request to quit to menu with confirmation."""
        self._confirm_dialog.show(
            "Quit Game?",
            "Your progress will be lost.",
            on_confirm=self._quit_to_menu,
            on_cancel=lambda: None
        )
    
    def _quit_to_menu(self) -> None:
        """Return to main menu."""
        self._game = None
        self._state = GameState.MENU
        self._input.reset()
        self._in_countdown = False
    
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
    
    def _on_toggle_ghost(self, enabled: bool) -> None:
        """Handle ghost piece toggle from settings."""
        self._renderer._show_ghost = enabled
        self._audio.play_sound("menu_select")
    
    def _on_toggle_particles(self, enabled: bool) -> None:
        """Handle particles toggle from settings."""
        self._renderer._particles_enabled = enabled
        self._audio.play_sound("menu_select")
    
    def _on_toggle_shake(self, enabled: bool) -> None:
        """Handle screen shake toggle from settings."""
        self._renderer._shake_enabled = enabled
        self._audio.play_sound("menu_select")
    
    def _request_quit(self) -> None:
        """Request to quit application with confirmation."""
        self._confirm_dialog.show(
            "Exit Game?",
            "Are you sure you want to exit?",
            on_confirm=self._quit,
            on_cancel=lambda: None
        )
    
    def _quit(self) -> None:
        """Quit the application."""
        self._running = False
    
    # Event handlers
    def _on_line_clear(self, event) -> None:
        lines = event.data.get("lines", 0)
        rows = event.data.get("rows", [])
        
        self._audio.play_line_clear(lines)
        self._renderer.trigger_line_clear(lines, rows)
        
        # Check for stage advancement based on score
        if self._game:
            old_stage = self._stage_manager.current_stage
            if self._stage_manager.update_score(self._game.score):
                # Stage changed! Trigger transition
                new_stage = self._stage_manager.current_stage
                stage_config = self._stage_manager.get_current_config()
                self._stage_transition.start(new_stage, stage_config.name)
    
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
    
    def _on_stage_change(self, event) -> None:
        """Handle stage/level change."""
        self._audio.play_level_up()
    
    def _on_stage_transition_complete(self) -> None:
        """Called when stage transition animation finishes."""
        pass
    
    def _on_game_over(self, event=None) -> None:
        self._audio.play_game_over()
        
        if self._game:
            # Record score to leaderboard
            position = self._save_manager.record_game(
                score=self._game.score,
                stage=self._stage_manager.current_stage,
                lines=self._game.lines,
                time_played=self._game_timer
            )
            
            self._game_over_menu.set_final_stats(
                self._game.score,
                self._game.lines,
                self._stage_manager.current_stage
            )
        
        self._state = GameState.GAME_OVER
    
    def _handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events."""
        if event.type == pygame.QUIT:
            self._request_quit()
            return
        
        # Handle window dragging (borderless window) - works even during loading
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicking on top area (drag zone)
            if event.pos[1] < DRAG_ZONE_HEIGHT and self._window_dragging_supported:
                self._dragging_window = True
                self._drag_offset = event.pos
                return
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_window = False
        
        if event.type == pygame.MOUSEMOTION and self._dragging_window and self._window_dragging_supported:
            x, y = pygame.display.get_window_position()
            new_x = x + event.pos[0] - self._drag_offset[0]
            new_y = y + event.pos[1] - self._drag_offset[1]
            pygame.display.set_window_position((new_x, new_y))
            return
        
        # Handle loading screen - no skipping allowed but continue processing window drag
        if self._in_loading:
            return
        
        # Handle story dialogue
        if self._in_story_dialogue and self._story_presentation.is_active:
            self._story_presentation.handle_event(event)
            return
        
        # Handle confirm dialog first
        if self._confirm_dialog.is_active:
            self._confirm_dialog.handle_event(event)
            return
        
        # Handle name entry screen
        if self._waiting_for_profile and self._name_entry.is_active:
            self._name_entry.handle_event(event)
            return
        
        # Handle leaderboard screen with back button
        if self._leaderboard_screen.is_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._back_button_rect.collidepoint(event.pos):
                    self._leaderboard_screen.close()
                    self._audio.play_sound("menu_select")
                    return
            self._leaderboard_screen.handle_event(event)
            return
        
        # Handle settings menu first if open with back button
        if self._in_settings:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._back_button_rect.collidepoint(event.pos):
                    self._close_settings()
                    return
            self._settings_menu.handle_event(event)
            return
        
        # During countdown, don't process other input
        if self._in_countdown:
            return
        
        if self._state == GameState.MENU:
            self._main_menu.handle_event(event)
        
        elif self._state == GameState.PLAYING:
            self._input.handle_event(event)
            
            # Check for pause
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._pause_game()
            
            # Check for menu button click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._menu_button_rect.collidepoint(event.pos):
                    self._pause_game()
                    self._audio.play_sound("menu_select")
        
        elif self._state == GameState.PAUSED:
            self._pause_menu.handle_event(event)
        
        elif self._state == GameState.GAME_OVER:
            self._game_over_menu.handle_event(event)
    
    def _update(self, dt: float) -> None:
        """Update game logic."""
        # Update loading screen
        if self._in_loading:
            self._loading_screen.update(dt)
            return
        
        # Update story dialogue
        if self._in_story_dialogue and self._story_presentation.is_active:
            self._story_presentation.update(dt)
            return
        
        # Update confirm dialog
        if self._confirm_dialog.is_active:
            self._confirm_dialog.update(dt)
            return
        
        # Update name entry
        if self._waiting_for_profile and self._name_entry.is_active:
            self._name_entry.update(dt)
            return
        
        # Update leaderboard screen
        if self._leaderboard_screen.is_active:
            self._leaderboard_screen.update(dt)
            return
        
        # Update settings menu if open
        if self._in_settings:
            self._settings_menu.update(dt)
            return
        
        # Update countdown
        if self._in_countdown:
            self._countdown.update(dt)
            return
        
        # Update stage transition
        if self._stage_transition.is_active:
            self._stage_transition.update(dt)
        
        if self._state == GameState.PLAYING and self._game:
            # Update game timer
            self._game_timer += dt
            
            # Update stage manager transition
            self._stage_manager.update_transition(dt)
            
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
        # Render loading screen first
        if self._in_loading:
            self._loading_screen.draw()
            return
        
        # Render story dialogue on top of background
        if self._in_story_dialogue and self._story_presentation.is_active:
            self._screen.fill((15, 15, 25))
            self._story_presentation.draw()
            return
        
        # Render confirm dialog on top of everything
        if self._confirm_dialog.is_active:
            self._render_game_background()
            self._confirm_dialog.draw()
            return
        
        # Render name entry screen
        if self._waiting_for_profile and self._name_entry.is_active:
            self._name_entry.draw()
            return
        
        # Render leaderboard screen with back button
        if self._leaderboard_screen.is_active:
            self._leaderboard_screen.draw()
            self._draw_back_button()
            return
        
        # Render settings if open with back button
        if self._in_settings:
            if self._settings_return_state == GameState.PAUSED and self._game:
                self._renderer.render(self._game)
                overlay = pygame.Surface((self._screen.get_width(), self._screen.get_height()), pygame.SRCALPHA)
                overlay.fill((10, 10, 20, 200))
                self._screen.blit(overlay, (0, 0))
            self._settings_menu.draw()
            self._draw_back_button()
            return
        
        # Render countdown
        if self._in_countdown:
            self._screen.fill((15, 15, 25))
            self._countdown.draw()
            return
        
        if self._state == GameState.MENU:
            self._main_menu.draw()
            # Player info is now drawn by the new MainMenu class
        
        elif self._state == GameState.PLAYING and self._game:
            self._renderer.render(self._game)
            self._draw_gameplay_player_info()
            self._draw_stage_info()
            self._draw_timer()
            self._draw_menu_button()
            
            # Draw stage transition on top
            if self._stage_transition.is_active:
                self._stage_transition.draw()
        
        elif self._state == GameState.PAUSED and self._game:
            self._renderer.render(self._game)
            self._pause_menu.draw()
        
        elif self._state == GameState.GAME_OVER and self._game:
            self._renderer.render(self._game)
            self._game_over_menu.draw()
    
    def _render_game_background(self) -> None:
        """Render game in background for dialogs."""
        if self._state == GameState.PLAYING and self._game:
            self._renderer.render(self._game)
        elif self._state == GameState.PAUSED and self._game:
            self._renderer.render(self._game)
        elif self._state == GameState.MENU:
            self._main_menu.draw()
        else:
            self._screen.fill((15, 15, 25))
    
    def _draw_player_info(self) -> None:
        """Draw current player info on menu."""
        player = self._save_manager.current_player
        if player:
            font = pygame.font.Font(None, 28)
            text = f"Player: {player.name}"
            surf = font.render(text, True, (150, 200, 255))
            self._screen.blit(surf, (20, self._screen.get_height() - 40))
    
    def _draw_stage_info(self) -> None:
        """Draw stage information during gameplay."""
        font = pygame.font.Font(None, 28)
        stage_text = f"STAGE {self._stage_manager.current_stage} - {self._stage_manager.stage_name}"
        surf = font.render(stage_text, True, (200, 200, 220))
        # Position in right panel area
        self._screen.blit(surf, (self._screen.get_width() - 250, 320))
    
    def _draw_timer(self) -> None:
        """Draw game timer."""
        font = pygame.font.Font(None, 32)
        minutes = int(self._game_timer // 60)
        seconds = int(self._game_timer % 60)
        time_text = f"{minutes:02d}:{seconds:02d}"
        surf = font.render(time_text, True, (180, 180, 200))
        self._screen.blit(surf, (self._screen.get_width() - 80, 20))
    
    def _draw_gameplay_player_info(self) -> None:
        """Draw player info (name + circular avatar) in upper left during gameplay."""
        player = self._save_manager.current_player
        if not player:
            return
        
        # Avatar position - use larger size from settings
        avatar_size = AVATAR_SIZE_GAMEPLAY
        avatar_x = 20
        avatar_y = 20
        
        # Draw circular avatar with manga-style frame
        pygame.draw.circle(self._screen, (50, 45, 70), (avatar_x + avatar_size // 2, avatar_y + avatar_size // 2), avatar_size // 2 + 5)
        
        # Get player avatar surface (PlayerProfile always has this method)
        avatar_surface = player.get_avatar_surface()
        if avatar_surface:
            # Scale and clip to circle
            scaled = pygame.transform.smoothscale(avatar_surface, (avatar_size, avatar_size))
            # Create circular mask
            mask = pygame.Surface((avatar_size, avatar_size), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (avatar_size // 2, avatar_size // 2), avatar_size // 2)
            scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._screen.blit(scaled, (avatar_x, avatar_y))
        else:
            # Default avatar - draw a simple manga-style silhouette
            pygame.draw.circle(self._screen, (70, 60, 100), (avatar_x + avatar_size // 2, avatar_y + avatar_size // 2), avatar_size // 2)
            # Draw simple user icon
            font = pygame.font.Font(None, avatar_size // 2)
            icon = font.render("?", True, (150, 140, 180))
            self._screen.blit(icon, (avatar_x + (avatar_size - icon.get_width()) // 2, avatar_y + (avatar_size - icon.get_height()) // 2))
        
        # Draw accent frame - modern blue
        pygame.draw.circle(self._screen, ACCENT_COLOR_BLUE, (avatar_x + avatar_size // 2, avatar_y + avatar_size // 2), avatar_size // 2 + 3, 3)
        
        # Draw player name next to avatar
        font = pygame.font.Font(None, 28)
        name_surf = font.render(player.name, True, (255, 255, 255))
        self._screen.blit(name_surf, (avatar_x + avatar_size + 15, avatar_y + (avatar_size - name_surf.get_height()) // 2))
    
    def _draw_menu_button(self) -> None:
        """Draw a clickable menu button in the upper right corner."""
        btn_width = 60
        btn_height = 30
        btn_x = self._screen.get_width() - btn_width - 20
        btn_y = 55  # Below the timer
        
        self._menu_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        
        # Check if mouse is hovering
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self._menu_button_rect.collidepoint(mouse_pos)
        
        # Draw button
        color = (80, 80, 120) if is_hovered else (50, 50, 70)
        pygame.draw.rect(self._screen, color, self._menu_button_rect, border_radius=8)
        pygame.draw.rect(self._screen, (100, 140, 200), self._menu_button_rect, 2, border_radius=8)
        
        # Draw text
        font = pygame.font.Font(None, 22)
        text = font.render("MENU", True, (200, 200, 220))
        text_x = btn_x + (btn_width - text.get_width()) // 2
        text_y = btn_y + (btn_height - text.get_height()) // 2
        self._screen.blit(text, (text_x, text_y))
    
    def _draw_back_button(self) -> None:
        """Draw a back arrow button in the top-left corner."""
        btn_size = 40
        self._back_button_rect = pygame.Rect(20, 20, btn_size, btn_size)
        
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self._back_button_rect.collidepoint(mouse_pos)
        
        # Draw button
        color = (70, 65, 95) if is_hovered else (45, 42, 60)
        pygame.draw.rect(self._screen, color, self._back_button_rect, border_radius=10)
        
        if is_hovered:
            pygame.draw.rect(self._screen, ACCENT_COLOR_BLUE, self._back_button_rect, 2, border_radius=10)
        else:
            pygame.draw.rect(self._screen, (70, 65, 90), self._back_button_rect, 1, border_radius=10)
        
        # Draw arrow icon
        font = pygame.font.Font(None, 28)
        arrow = font.render("←", True, (200, 195, 220) if not is_hovered else (255, 255, 255))
        arrow_x = self._back_button_rect.x + (btn_size - arrow.get_width()) // 2
        arrow_y = self._back_button_rect.y + (btn_size - arrow.get_height()) // 2
        self._screen.blit(arrow, (arrow_x, arrow_y))
    
    def _get_target_fps(self) -> int:
        """Get the target FPS based on current game state (adaptive frame rate)."""
        # Full 60 FPS during gameplay
        if self._state == GameState.PLAYING and not self._in_countdown:
            return FPS_GAMEPLAY
        
        # 30 FPS for menus and other states (sufficient for UI)
        return FPS_MENU
    
    def run(self) -> None:
        """Run the main game loop with adaptive frame rate."""
        last_time = time.perf_counter()
        
        try:
            while self._running:
                # Calculate delta time
                current_time = time.perf_counter()
                dt = current_time - last_time
                last_time = current_time
                
                # Cap delta time to prevent spiral of death
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
                
                # Adaptive frame rate - reduce CPU usage when not actively playing
                target_fps = self._get_target_fps()
                self._clock.tick(target_fps)
        
        finally:
            # Always cleanup properly (ensure resources are freed)
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up resources properly on exit."""
        # Stop audio
        try:
            pygame.mixer.stop()
            pygame.mixer.quit()
        except Exception:
            pass
        
        # Save any pending data
        try:
            self._save_manager.save_all()
        except Exception:
            pass
        
        # Clear cached surfaces
        self._cached_surfaces.clear()
        
        # Quit pygame
        pygame.quit()


def main():
    """Entry point."""
    app = TetrisApp()
    app.run()


if __name__ == "__main__":
    main()
