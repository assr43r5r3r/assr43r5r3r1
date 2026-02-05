"""
Main Tetris game logic.
Coordinates all game systems.
"""

from typing import Optional, Tuple, Callable, List
from dataclasses import dataclass
from enum import Enum, auto
import time

from .board import Board
from .pieces import Piece, create_piece, PIECE_NAMES
from .srs import SRS, detect_tspin
from .bag import Bag
from .scoring import Scoring, ScoreEvent
from .replay import ReplayRecorder, ReplayPlayer, InputAction


class GameStatus(Enum):
    """Game status states."""
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


@dataclass
class GameState:
    """Snapshot of game state for events."""
    status: GameStatus
    current_piece: Optional[Piece]
    hold_piece: Optional[str]
    can_hold: bool
    next_pieces: List[str]
    score: int
    lines: int
    level: int
    combo: int
    is_back_to_back: bool


class TetrisGame:
    """
    Main Tetris game controller.
    
    Handles all game logic including piece movement, rotation,
    line clearing, scoring, and game state management.
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        start_level: int = 1,
        das_delay: int = 10,
        arr_rate: int = 2,
        lock_delay: int = 30,
        max_lock_resets: int = 15,
        gravity_table: Optional[dict] = None
    ):
        """
        Initialize a new game.
        
        Args:
            seed: Random seed for deterministic gameplay
            start_level: Starting level (affects gravity)
            das_delay: Delayed Auto Shift delay in frames
            arr_rate: Auto Repeat Rate in frames
            lock_delay: Lock delay in frames
            max_lock_resets: Maximum lock delay resets
            gravity_table: Custom gravity table (level -> frames per drop)
        """
        # Use current time as seed if not provided
        self._seed = seed if seed is not None else int(time.time() * 1000) % (2**31)
        
        # Core game objects
        self._board = Board()
        self._bag = Bag(self._seed)
        self._scoring = Scoring()
        self._scoring.level = start_level
        
        # Timing settings
        self._das_delay = das_delay
        self._arr_rate = arr_rate
        self._lock_delay_max = lock_delay
        self._max_lock_resets = max_lock_resets
        
        # Default gravity table
        self._gravity_table = gravity_table or {
            0: 48, 1: 43, 2: 38, 3: 33, 4: 28,
            5: 23, 6: 18, 7: 13, 8: 8, 9: 6,
            10: 5, 11: 5, 12: 5, 13: 4, 14: 4,
            15: 4, 16: 3, 17: 3, 18: 3, 19: 2, 20: 1
        }
        
        # Game state
        self._status = GameStatus.PLAYING
        self._current_piece: Optional[Piece] = None
        self._hold_piece: Optional[str] = None
        self._can_hold = True
        self._last_kick_index = 0
        
        # Timing counters
        self._gravity_counter = 0
        self._lock_delay_counter = 0
        self._lock_reset_count = 0
        self._is_on_ground = False
        
        # DAS/ARR state
        self._das_left = 0
        self._das_right = 0
        self._das_direction = 0  # -1 = left, 0 = none, 1 = right
        
        # Replay recording
        self._recorder = ReplayRecorder(self._seed, start_level)
        self._replay_player: Optional[ReplayPlayer] = None
        
        # Event callbacks
        self._on_piece_spawn: Optional[Callable] = None
        self._on_piece_move: Optional[Callable] = None
        self._on_piece_rotate: Optional[Callable] = None
        self._on_piece_lock: Optional[Callable] = None
        self._on_piece_hold: Optional[Callable] = None
        self._on_hard_drop: Optional[Callable] = None
        self._on_line_clear: Optional[Callable] = None
        self._on_tspin: Optional[Callable] = None
        self._on_combo: Optional[Callable] = None
        self._on_back_to_back: Optional[Callable] = None
        self._on_perfect_clear: Optional[Callable] = None
        self._on_level_up: Optional[Callable] = None
        self._on_game_over: Optional[Callable] = None
        
        # Spawn first piece
        self._spawn_piece()
    
    def _spawn_piece(self) -> bool:
        """
        Spawn a new piece.
        
        Returns:
            True if piece spawned successfully, False if topped out
        """
        piece_type = self._bag.next()
        
        # Spawn position: center top, adjusted for I piece
        spawn_x = 3
        spawn_y = 0 if piece_type == "I" else 1
        
        self._current_piece = Piece(piece_type, spawn_x, spawn_y, 0)
        self._can_hold = True
        self._last_kick_index = 0
        
        # Reset lock delay
        self._lock_delay_counter = 0
        self._lock_reset_count = 0
        self._is_on_ground = False
        self._gravity_counter = 0
        
        # Check for top-out
        if self._board.is_topped_out(self._current_piece):
            self._status = GameStatus.GAME_OVER
            if self._on_game_over:
                self._on_game_over()
            return False
        
        if self._on_piece_spawn:
            self._on_piece_spawn(piece_type)
        
        return True
    
    def _get_gravity(self) -> int:
        """Get current gravity (frames per cell drop)."""
        level = min(self._scoring.level, 20)
        return self._gravity_table.get(level, 1)
    
    def update(self) -> None:
        """
        Update game logic for one frame.
        Should be called at 60 FPS.
        """
        if self._status != GameStatus.PLAYING:
            return
        
        if self._current_piece is None:
            return
        
        # Check if piece is on ground
        was_on_ground = self._is_on_ground
        self._is_on_ground = not self._board.is_valid_position(
            self._current_piece,
            y=self._current_piece.y + 1
        )
        
        # Handle gravity
        if not self._is_on_ground:
            self._gravity_counter += 1
            gravity = self._get_gravity()
            
            while self._gravity_counter >= gravity:
                self._gravity_counter -= gravity
                if self._board.is_valid_position(self._current_piece, y=self._current_piece.y + 1):
                    self._current_piece.y += 1
                else:
                    break
        
        # Handle lock delay
        if self._is_on_ground:
            self._lock_delay_counter += 1
            
            if self._lock_delay_counter >= self._lock_delay_max:
                self._lock_piece()
        
        # End frame for replay recording
        self._recorder.end_frame()
    
    def _reset_lock_delay(self) -> bool:
        """
        Reset lock delay if allowed.
        
        Returns:
            True if reset was successful
        """
        if self._lock_reset_count < self._max_lock_resets:
            self._lock_delay_counter = 0
            self._lock_reset_count += 1
            return True
        return False
    
    def _lock_piece(self) -> None:
        """Lock the current piece and handle line clears."""
        if self._current_piece is None:
            return
        
        # Detect T-Spin before locking
        tspin_type = detect_tspin(
            self._current_piece,
            self._board.is_cell_filled,
            self._last_kick_index
        )
        
        # Lock piece into board
        self._board.lock_piece(self._current_piece)
        
        if self._on_piece_lock:
            self._on_piece_lock(self._current_piece.piece_type)
        
        # Clear lines
        lines_cleared, cleared_rows = self._board.clear_lines()
        
        # Check for perfect clear
        is_perfect = self._board.is_empty() and lines_cleared > 0
        
        # Calculate score
        event = ScoreEvent(
            lines_cleared=lines_cleared,
            is_tspin=(tspin_type == "full"),
            is_tspin_mini=(tspin_type == "mini"),
            is_perfect_clear=is_perfect,
            level=self._scoring.level
        )
        
        points = self._scoring.calculate_score(event)
        
        # Fire events
        if lines_cleared > 0:
            if self._on_line_clear:
                self._on_line_clear(lines_cleared, cleared_rows)
            
            if tspin_type != "none" and self._on_tspin:
                self._on_tspin(tspin_type, lines_cleared)
            
            if self._scoring.combo > 0 and self._on_combo:
                self._on_combo(self._scoring.combo)
            
            if self._scoring.is_back_to_back and self._on_back_to_back:
                self._on_back_to_back()
            
            if is_perfect and self._on_perfect_clear:
                self._on_perfect_clear()
            
            # Check for level up
            if self._scoring.update_level() and self._on_level_up:
                self._on_level_up(self._scoring.level)
        
        # Spawn next piece
        self._current_piece = None
        self._spawn_piece()
    
    def move_left(self) -> bool:
        """
        Move piece left.
        
        Returns:
            True if move succeeded
        """
        if self._current_piece is None or self._status != GameStatus.PLAYING:
            return False
        
        if self._board.is_valid_position(self._current_piece, x=self._current_piece.x - 1):
            self._current_piece.x -= 1
            self._recorder.record_action(InputAction.MOVE_LEFT)
            
            if self._is_on_ground:
                self._reset_lock_delay()
            
            if self._on_piece_move:
                self._on_piece_move(-1, 0)
            
            return True
        return False
    
    def move_right(self) -> bool:
        """
        Move piece right.
        
        Returns:
            True if move succeeded
        """
        if self._current_piece is None or self._status != GameStatus.PLAYING:
            return False
        
        if self._board.is_valid_position(self._current_piece, x=self._current_piece.x + 1):
            self._current_piece.x += 1
            self._recorder.record_action(InputAction.MOVE_RIGHT)
            
            if self._is_on_ground:
                self._reset_lock_delay()
            
            if self._on_piece_move:
                self._on_piece_move(1, 0)
            
            return True
        return False
    
    def soft_drop(self) -> bool:
        """
        Soft drop (move down one cell).
        
        Returns:
            True if drop succeeded
        """
        if self._current_piece is None or self._status != GameStatus.PLAYING:
            return False
        
        if self._board.is_valid_position(self._current_piece, y=self._current_piece.y + 1):
            self._current_piece.y += 1
            self._gravity_counter = 0
            self._scoring.add_soft_drop_points(1)
            self._recorder.record_action(InputAction.SOFT_DROP)
            
            if self._on_piece_move:
                self._on_piece_move(0, 1)
            
            return True
        return False
    
    def hard_drop(self) -> int:
        """
        Hard drop (instant drop and lock).
        
        Returns:
            Number of cells dropped
        """
        if self._current_piece is None or self._status != GameStatus.PLAYING:
            return 0
        
        drop_distance = self._board.get_drop_distance(self._current_piece)
        self._current_piece.y += drop_distance
        
        self._recorder.record_action(InputAction.HARD_DROP)
        
        if self._on_hard_drop:
            self._on_hard_drop(drop_distance)
        
        # Create score event for hard drop points
        event = ScoreEvent(
            is_hard_drop=True,
            drop_distance=drop_distance,
            level=self._scoring.level
        )
        self._scoring.calculate_score(event)
        
        # Lock immediately
        self._lock_piece()
        
        return drop_distance
    
    def rotate_cw(self) -> bool:
        """
        Rotate piece clockwise.
        
        Returns:
            True if rotation succeeded
        """
        return self._rotate(SRS.rotate_cw)
    
    def rotate_ccw(self) -> bool:
        """
        Rotate piece counter-clockwise.
        
        Returns:
            True if rotation succeeded
        """
        return self._rotate(SRS.rotate_ccw)
    
    def rotate_180(self) -> bool:
        """
        Rotate piece 180 degrees.
        
        Returns:
            True if rotation succeeded
        """
        return self._rotate(SRS.rotate_180)
    
    def _rotate(self, rotation_fn: Callable) -> bool:
        """
        Perform rotation with wall kicks.
        
        Args:
            rotation_fn: Function to calculate target rotation
        
        Returns:
            True if rotation succeeded
        """
        if self._current_piece is None or self._status != GameStatus.PLAYING:
            return False
        
        target_rotation = rotation_fn(self._current_piece)
        
        # Try rotation with wall kicks
        def collision_check(x: int, y: int, rot: int) -> bool:
            return self._board.check_collision(
                x, y, rot, self._current_piece.piece_type
            )
        
        result = SRS.try_rotation(
            self._current_piece,
            target_rotation,
            collision_check
        )
        
        if result is not None:
            new_x, new_y, kick_index = result
            self._current_piece.x = new_x
            self._current_piece.y = new_y
            self._current_piece.rotation = target_rotation
            self._last_kick_index = kick_index
            
            self._recorder.record_action(InputAction.ROTATE_CW)
            
            if self._is_on_ground:
                self._reset_lock_delay()
            
            if self._on_piece_rotate:
                self._on_piece_rotate(target_rotation, kick_index)
            
            return True
        
        return False
    
    def hold(self) -> bool:
        """
        Hold current piece.
        
        Returns:
            True if hold succeeded
        """
        if self._current_piece is None or self._status != GameStatus.PLAYING:
            return False
        
        if not self._can_hold:
            return False
        
        current_type = self._current_piece.piece_type
        
        if self._hold_piece is None:
            # First hold - get new piece from bag
            self._hold_piece = current_type
            self._current_piece = None
            self._spawn_piece()
        else:
            # Swap with held piece
            self._current_piece = create_piece(self._hold_piece)
            self._hold_piece = current_type
            
            # Check if swapped piece can spawn
            if self._board.is_topped_out(self._current_piece):
                self._status = GameStatus.GAME_OVER
                if self._on_game_over:
                    self._on_game_over()
                return False
        
        self._can_hold = False
        self._last_kick_index = 0
        self._lock_delay_counter = 0
        self._lock_reset_count = 0
        
        self._recorder.record_action(InputAction.HOLD)
        
        if self._on_piece_hold:
            self._on_piece_hold(self._hold_piece)
        
        return True
    
    def pause(self) -> None:
        """Pause the game."""
        if self._status == GameStatus.PLAYING:
            self._status = GameStatus.PAUSED
    
    def resume(self) -> None:
        """Resume the game."""
        if self._status == GameStatus.PAUSED:
            self._status = GameStatus.PLAYING
    
    def reset(self, seed: Optional[int] = None) -> None:
        """
        Reset the game.
        
        Args:
            seed: New seed (uses previous seed if None)
        """
        if seed is not None:
            self._seed = seed
        
        self._board.reset()
        self._bag.reset(self._seed)
        self._scoring.reset()
        
        self._status = GameStatus.PLAYING
        self._current_piece = None
        self._hold_piece = None
        self._can_hold = True
        self._last_kick_index = 0
        
        self._gravity_counter = 0
        self._lock_delay_counter = 0
        self._lock_reset_count = 0
        self._is_on_ground = False
        
        self._recorder = ReplayRecorder(self._seed, self._scoring.level)
        
        self._spawn_piece()
    
    # Event callback setters
    def on_piece_spawn(self, callback: Callable) -> None:
        self._on_piece_spawn = callback
    
    def on_piece_move(self, callback: Callable) -> None:
        self._on_piece_move = callback
    
    def on_piece_rotate(self, callback: Callable) -> None:
        self._on_piece_rotate = callback
    
    def on_piece_lock(self, callback: Callable) -> None:
        self._on_piece_lock = callback
    
    def on_piece_hold(self, callback: Callable) -> None:
        self._on_piece_hold = callback
    
    def on_hard_drop(self, callback: Callable) -> None:
        self._on_hard_drop = callback
    
    def on_line_clear(self, callback: Callable) -> None:
        self._on_line_clear = callback
    
    def on_tspin(self, callback: Callable) -> None:
        self._on_tspin = callback
    
    def on_combo(self, callback: Callable) -> None:
        self._on_combo = callback
    
    def on_back_to_back(self, callback: Callable) -> None:
        self._on_back_to_back = callback
    
    def on_perfect_clear(self, callback: Callable) -> None:
        self._on_perfect_clear = callback
    
    def on_level_up(self, callback: Callable) -> None:
        self._on_level_up = callback
    
    def on_game_over(self, callback: Callable) -> None:
        self._on_game_over = callback
    
    # Properties
    @property
    def board(self) -> Board:
        return self._board
    
    @property
    def current_piece(self) -> Optional[Piece]:
        return self._current_piece
    
    @property
    def hold_piece(self) -> Optional[str]:
        return self._hold_piece
    
    @property
    def can_hold(self) -> bool:
        return self._can_hold
    
    @property
    def next_pieces(self) -> List[str]:
        return self._bag.peek(6)
    
    @property
    def ghost_y(self) -> int:
        if self._current_piece:
            return self._board.get_ghost_position(self._current_piece)
        return 0
    
    @property
    def score(self) -> int:
        return self._scoring.score
    
    @property
    def lines(self) -> int:
        return self._scoring.lines
    
    @property
    def level(self) -> int:
        return self._scoring.level
    
    @property
    def combo(self) -> int:
        return self._scoring.combo
    
    @property
    def is_back_to_back(self) -> bool:
        return self._scoring.is_back_to_back
    
    @property
    def status(self) -> GameStatus:
        return self._status
    
    @property
    def seed(self) -> int:
        return self._seed
    
    @property
    def lock_delay_progress(self) -> float:
        """Get lock delay progress (0.0 to 1.0)."""
        if self._lock_delay_max == 0:
            return 0.0
        return min(1.0, self._lock_delay_counter / self._lock_delay_max)
    
    def get_replay(self) -> 'ReplayRecorder':
        """Get the replay recorder."""
        return self._recorder
    
    def get_state(self) -> GameState:
        """Get current game state snapshot."""
        return GameState(
            status=self._status,
            current_piece=self._current_piece.copy() if self._current_piece else None,
            hold_piece=self._hold_piece,
            can_hold=self._can_hold,
            next_pieces=self.next_pieces,
            score=self.score,
            lines=self.lines,
            level=self.level,
            combo=self.combo,
            is_back_to_back=self.is_back_to_back
        )
    
    def get_stats(self) -> dict:
        """Get scoring statistics."""
        return self._scoring.get_stats()
