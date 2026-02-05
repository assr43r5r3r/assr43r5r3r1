"""
Main renderer for the Tetris game.
"""

from typing import Optional, Tuple, List, Dict
import math

try:
    import pygame
except ImportError:
    import pygame_ce as pygame

from src.tetris.game import TetrisGame, GameStatus
from src.tetris.pieces import Piece, PIECE_SHAPES
from .particles import ParticleSystem, ParticleEmitter
from src.util.math_utils import lerp, ease_out_quad


class ScreenShake:
    """Screen shake effect."""
    
    def __init__(self, decay: float = 0.85, max_offset: float = 15):
        self.intensity = 0.0
        self.decay = decay
        self.max_offset = max_offset
        self._offset_x = 0.0
        self._offset_y = 0.0
    
    def trigger(self, intensity: float) -> None:
        """Trigger screen shake."""
        self.intensity = min(self.intensity + intensity, 1.0)
    
    def update(self) -> Tuple[int, int]:
        """
        Update shake and get offset.
        
        Returns:
            (x_offset, y_offset) in pixels
        """
        if self.intensity > 0.01:
            import random
            angle = random.uniform(0, 2 * math.pi)
            magnitude = self.intensity * self.max_offset
            
            self._offset_x = math.cos(angle) * magnitude
            self._offset_y = math.sin(angle) * magnitude
            
            self.intensity *= self.decay
        else:
            self.intensity = 0
            self._offset_x = 0
            self._offset_y = 0
        
        return int(self._offset_x), int(self._offset_y)


class Renderer:
    """
    Main game renderer.
    
    Handles all visual rendering including the board, pieces,
    particles, UI, and visual effects.
    """
    
    def __init__(
        self,
        screen: pygame.Surface,
        cell_size: int = 30,
        palette: Dict[str, Tuple[int, int, int]] = None
    ):
        """
        Initialize renderer.
        
        Args:
            screen: Pygame surface to render to
            cell_size: Size of each cell in pixels
            palette: Color palette dictionary
        """
        self._screen = screen
        self._cell_size = cell_size
        
        # Default palette
        self._palette = palette or {
            "I": (0, 240, 240),
            "O": (240, 240, 0),
            "T": (160, 0, 240),
            "S": (0, 240, 0),
            "Z": (240, 0, 0),
            "J": (0, 0, 240),
            "L": (240, 160, 0),
            "ghost": (128, 128, 128),
            "background": (20, 20, 30),
            "grid_line": (40, 40, 60),
            "ui_text": (255, 255, 255),
            "ui_accent": (100, 200, 255),
            "glow": (255, 255, 255),
        }
        
        # Screen dimensions
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        # Grid positioning
        self._grid_width = 10
        self._grid_height = 20
        grid_pixel_width = self._grid_width * cell_size
        grid_pixel_height = self._grid_height * cell_size
        
        # Center the grid
        self._grid_x = (self._width - grid_pixel_width) // 2
        self._grid_y = (self._height - grid_pixel_height) // 2
        
        # Particle system
        self._particles = ParticleSystem()
        
        # Screen shake
        self._shake = ScreenShake()
        
        # Animation state
        self._line_clear_anim: List[Tuple[int, float]] = []  # [(row, progress), ...]
        self._lock_flash = 0.0
        self._clearing_rows: List[int] = []  # Rows being cleared with animation
        self._clear_anim_progress = 0.0  # 0 to 1
        
        # Visual settings
        self._show_ghost = True
        self._show_grid = True
        self._particles_enabled = True
        self._shake_enabled = True
        
        # Fonts
        pygame.font.init()
        self._font_large = pygame.font.Font(None, 48)
        self._font_medium = pygame.font.Font(None, 36)
        self._font_small = pygame.font.Font(None, 24)
        
        # Pre-render some surfaces
        self._cell_surfaces: Dict[str, pygame.Surface] = {}
        self._create_cell_surfaces()
    
    def _create_cell_surfaces(self) -> None:
        """Create pre-rendered cell surfaces."""
        for piece_type in ["I", "O", "T", "S", "Z", "J", "L"]:
            surface = self._create_cell_surface(self._palette[piece_type])
            self._cell_surfaces[piece_type] = surface
        
        # Ghost piece surface
        ghost_surface = self._create_cell_surface(
            self._palette["ghost"], 
            alpha=100
        )
        self._cell_surfaces["ghost"] = ghost_surface
    
    def _create_cell_surface(
        self, 
        color: Tuple[int, int, int], 
        alpha: int = 255
    ) -> pygame.Surface:
        """
        Create a single cell surface with modern flat style.
        
        Args:
            color: Base color
            alpha: Transparency
        
        Returns:
            Rendered cell surface
        """
        size = self._cell_size
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Main fill
        base_rect = pygame.Rect(1, 1, size - 2, size - 2)
        pygame.draw.rect(surface, (*color, alpha), base_rect)
        
        # Highlight (top and left edges)
        highlight = tuple(min(255, c + 40) for c in color)
        pygame.draw.line(surface, (*highlight, alpha), (1, 1), (size - 2, 1), 2)
        pygame.draw.line(surface, (*highlight, alpha), (1, 1), (1, size - 2), 2)
        
        # Shadow (bottom and right edges)
        shadow = tuple(max(0, c - 40) for c in color)
        pygame.draw.line(surface, (*shadow, alpha), (1, size - 2), (size - 2, size - 2), 2)
        pygame.draw.line(surface, (*shadow, alpha), (size - 2, 1), (size - 2, size - 2), 2)
        
        return surface
    
    def set_palette(self, palette: Dict[str, Tuple[int, int, int]]) -> None:
        """Set a new color palette."""
        self._palette.update(palette)
        self._create_cell_surfaces()
    
    def render(self, game: TetrisGame, alpha: float = 1.0) -> None:
        """
        Render the complete game frame.
        
        Args:
            game: Game state to render
            alpha: Interpolation factor (0.0 to 1.0)
        """
        # Get screen shake offset
        shake_x, shake_y = self._shake.update() if self._shake_enabled else (0, 0)
        
        # Clear screen
        self._screen.fill(self._palette["background"])
        
        # Draw grid background
        if self._show_grid:
            self._draw_grid(shake_x, shake_y)
        
        # Draw locked pieces
        self._draw_board(game.board, shake_x, shake_y)
        
        # Draw ghost piece
        if self._show_ghost and game.current_piece:
            self._draw_ghost(game.current_piece, game.ghost_y, shake_x, shake_y)
        
        # Draw current piece
        if game.current_piece:
            self._draw_piece(game.current_piece, shake_x, shake_y)
        
        # Draw particles
        if self._particles_enabled:
            self._particles.draw(self._screen, shake_x, shake_y)
        
        # Draw hold piece
        self._draw_hold(game.hold_piece, game.can_hold)
        
        # Draw next pieces
        self._draw_next(game.next_pieces)
        
        # Draw score/stats
        self._draw_stats(game)
        
        # Draw game over overlay
        if game.status == GameStatus.GAME_OVER:
            self._draw_game_over()
        elif game.status == GameStatus.PAUSED:
            self._draw_paused()
    
    def _draw_grid(self, offset_x: int, offset_y: int) -> None:
        """Draw the grid lines."""
        color = self._palette["grid_line"]
        
        # Vertical lines
        for x in range(self._grid_width + 1):
            px = self._grid_x + x * self._cell_size + offset_x
            pygame.draw.line(
                self._screen, color,
                (px, self._grid_y + offset_y),
                (px, self._grid_y + self._grid_height * self._cell_size + offset_y)
            )
        
        # Horizontal lines
        for y in range(self._grid_height + 1):
            py = self._grid_y + y * self._cell_size + offset_y
            pygame.draw.line(
                self._screen, color,
                (self._grid_x + offset_x, py),
                (self._grid_x + self._grid_width * self._cell_size + offset_x, py)
            )
        
        # Border
        border_rect = pygame.Rect(
            self._grid_x + offset_x - 2,
            self._grid_y + offset_y - 2,
            self._grid_width * self._cell_size + 4,
            self._grid_height * self._cell_size + 4
        )
        pygame.draw.rect(self._screen, self._palette["ui_accent"], border_rect, 2)
    
    def _draw_board(self, board, offset_x: int, offset_y: int) -> None:
        """Draw the locked pieces on the board with line clear animation."""
        hidden_rows = board.hidden_rows
        
        for y in range(board.total_height):
            for x in range(board.width):
                cell = board.get_cell(x, y)
                if cell is not None:
                    # Only draw visible rows
                    visible_y = y - hidden_rows
                    if visible_y >= 0:
                        # Check if this row is being cleared
                        if y in self._clearing_rows:
                            # Flash effect during clear animation:
                            # - Fade out over animation progress (1.0 -> 0.0)
                            # - Oscillate brightness with sin wave (20 = ~3 flashes during animation)
                            # - 0.5 + 0.5*sin gives range [0, 1] for smooth pulsing
                            fade = 1.0 - self._clear_anim_progress
                            pulse = 0.5 + 0.5 * math.sin(self._clear_anim_progress * 20)
                            alpha = int(255 * fade * pulse)
                            self._draw_cell_with_alpha(
                                x, visible_y, cell,
                                offset_x, offset_y, alpha
                            )
                        else:
                            self._draw_cell(
                                x, visible_y, cell,
                                offset_x, offset_y
                            )
    
    def _draw_cell_with_alpha(
        self,
        grid_x: int,
        grid_y: int,
        piece_type: str,
        offset_x: int = 0,
        offset_y: int = 0,
        alpha: int = 255
    ) -> None:
        """Draw a single cell with alpha transparency."""
        surface = self._cell_surfaces.get(piece_type)
        if surface:
            px = self._grid_x + grid_x * self._cell_size + offset_x
            py = self._grid_y + grid_y * self._cell_size + offset_y
            
            # Create a copy with alpha
            cell_copy = surface.copy()
            cell_copy.set_alpha(alpha)
            self._screen.blit(cell_copy, (px, py))
            
            # Draw flash effect
            if alpha > 100:
                flash = pygame.Surface((self._cell_size, self._cell_size), pygame.SRCALPHA)
                flash.fill((255, 255, 255, min(150, alpha // 2)))
                self._screen.blit(flash, (px, py))
    
    def _draw_cell(
        self, 
        grid_x: int, 
        grid_y: int, 
        piece_type: str,
        offset_x: int = 0,
        offset_y: int = 0
    ) -> None:
        """Draw a single cell."""
        surface = self._cell_surfaces.get(piece_type)
        if surface:
            px = self._grid_x + grid_x * self._cell_size + offset_x
            py = self._grid_y + grid_y * self._cell_size + offset_y
            self._screen.blit(surface, (px, py))
    
    def _draw_piece(self, piece: Piece, offset_x: int, offset_y: int) -> None:
        """Draw the current active piece."""
        hidden_rows = 4  # Adjust for hidden rows
        
        for cell_x, cell_y in piece.get_cells():
            visible_y = cell_y - hidden_rows
            if visible_y >= 0:
                self._draw_cell(cell_x, visible_y, piece.piece_type, offset_x, offset_y)
    
    def _draw_ghost(self, piece: Piece, ghost_y: int, 
                    offset_x: int, offset_y: int) -> None:
        """Draw the ghost piece."""
        hidden_rows = 4
        shape = PIECE_SHAPES[piece.piece_type][piece.rotation]
        
        for dx, dy in shape:
            cell_x = piece.x + dx
            cell_y = ghost_y + dy
            visible_y = cell_y - hidden_rows
            
            if visible_y >= 0:
                surface = self._cell_surfaces["ghost"]
                px = self._grid_x + cell_x * self._cell_size + offset_x
                py = self._grid_y + visible_y * self._cell_size + offset_y
                self._screen.blit(surface, (px, py))
    
    def _draw_hold(self, hold_piece: Optional[str], can_hold: bool) -> None:
        """Draw the hold piece display."""
        # Position to the left of the grid
        box_x = self._grid_x - 140
        box_y = self._grid_y
        box_size = 120
        
        # Draw box
        box_rect = pygame.Rect(box_x, box_y, box_size, box_size)
        pygame.draw.rect(self._screen, self._palette["grid_line"], box_rect, 2)
        
        # Draw label
        label = self._font_small.render("HOLD", True, self._palette["ui_text"])
        self._screen.blit(label, (box_x + (box_size - label.get_width()) // 2, box_y - 25))
        
        # Draw piece if holding
        if hold_piece:
            color = self._palette[hold_piece]
            if not can_hold:
                # Dim the color if can't hold
                color = tuple(c // 2 for c in color)
            
            self._draw_mini_piece(hold_piece, box_x + 20, box_y + 20, color)
    
    def _draw_next(self, next_pieces: List[str]) -> None:
        """Draw the next pieces preview (3 pieces only)."""
        # Position to the right of the grid
        box_x = self._grid_x + self._grid_width * self._cell_size + 20
        box_y = self._grid_y
        box_width = 120
        box_height = 250  # Reduced height for 3 pieces
        
        # Draw box
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self._screen, self._palette["grid_line"], box_rect, 2)
        
        # Draw label
        label = self._font_small.render("NEXT", True, self._palette["ui_text"])
        self._screen.blit(label, (box_x + (box_width - label.get_width()) // 2, box_y - 25))
        
        # Draw only 3 pieces
        for i, piece_type in enumerate(next_pieces[:3]):
            color = self._palette[piece_type]
            self._draw_mini_piece(piece_type, box_x + 20, box_y + 20 + i * 75, color)
    
    def _draw_mini_piece(
        self, 
        piece_type: str, 
        x: int, 
        y: int, 
        color: Tuple[int, int, int]
    ) -> None:
        """Draw a miniature piece for hold/next display."""
        mini_size = 18
        shape = PIECE_SHAPES[piece_type][0]  # Use spawn rotation
        
        # Center the piece
        min_x = min(dx for dx, dy in shape)
        max_x = max(dx for dx, dy in shape)
        min_y = min(dy for dx, dy in shape)
        max_y = max(dy for dx, dy in shape)
        
        offset_x = (4 - (max_x - min_x + 1)) * mini_size // 2
        offset_y = (2 - (max_y - min_y + 1)) * mini_size // 2
        
        for dx, dy in shape:
            rect = pygame.Rect(
                x + (dx - min_x) * mini_size + offset_x,
                y + (dy - min_y) * mini_size + offset_y,
                mini_size - 1,
                mini_size - 1
            )
            pygame.draw.rect(self._screen, color, rect)
    
    def _draw_stats(self, game: TetrisGame) -> None:
        """Draw score and stats without level (stage is shown separately)."""
        x = self._grid_x - 140
        y = self._grid_y + 150
        
        stats = [
            ("SCORE", f"{game.score:,}"),
            ("LINES", str(game.lines)),
        ]
        
        if game.combo > 0:
            stats.append(("COMBO", str(game.combo)))
        
        if game.is_back_to_back:
            stats.append(("B2B", "YES"))
        
        for i, (label, value) in enumerate(stats):
            label_surface = self._font_small.render(label, True, self._palette["ui_accent"])
            value_surface = self._font_medium.render(value, True, self._palette["ui_text"])
            
            self._screen.blit(label_surface, (x, y + i * 50))
            self._screen.blit(value_surface, (x, y + i * 50 + 18))
    
    def _draw_game_over(self) -> None:
        """Draw game over overlay."""
        # Darken background
        overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self._screen.blit(overlay, (0, 0))
        
        # Game over text
        text = self._font_large.render("GAME OVER", True, (255, 100, 100))
        x = (self._width - text.get_width()) // 2
        y = (self._height - text.get_height()) // 2 - 30
        self._screen.blit(text, (x, y))
        
        # Restart hint
        hint = self._font_small.render("Press R to restart", True, self._palette["ui_text"])
        x = (self._width - hint.get_width()) // 2
        y = (self._height - hint.get_height()) // 2 + 30
        self._screen.blit(hint, (x, y))
    
    def _draw_paused(self) -> None:
        """Draw paused overlay."""
        # Darken background
        overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self._screen.blit(overlay, (0, 0))
        
        # Paused text
        text = self._font_large.render("PAUSED", True, self._palette["ui_accent"])
        x = (self._width - text.get_width()) // 2
        y = (self._height - text.get_height()) // 2
        self._screen.blit(text, (x, y))
    
    def update(self, dt: float) -> None:
        """
        Update visual effects.
        
        Args:
            dt: Delta time in seconds
        """
        self._particles.update(dt)
        
        # Update line clear animation
        if self._clearing_rows:
            self._clear_anim_progress += dt * 4  # Animation takes 0.25 seconds
            if self._clear_anim_progress >= 1.0:
                self._clearing_rows = []
                self._clear_anim_progress = 0.0
    
    def trigger_line_clear(self, lines: int, rows: List[int], 
                           colors: List[Tuple[int, int, int]] = None) -> None:
        """
        Trigger line clear effects.
        
        Args:
            lines: Number of lines cleared
            rows: List of row indices cleared
            colors: Optional colors for particles
        """
        # Start the line clear animation
        self._clearing_rows = rows.copy()
        self._clear_anim_progress = 0.0
        
        # Screen shake based on lines cleared
        shake_intensity = 0.1 * lines
        if lines == 4:  # Tetris
            shake_intensity = 0.5
        self._shake.trigger(shake_intensity)
        
        # Emit particles
        color = colors[0] if colors else self._palette["ui_accent"]
        for row in rows:
            # Adjust for hidden rows
            visible_row = row - 4
            if visible_row >= 0:
                self._particles.emit_line_clear(
                    self._grid_y + visible_row * self._cell_size,
                    self._cell_size,
                    self._grid_x,
                    self._grid_width,
                    color
                )
    
    def trigger_hard_drop(self, x: int, y: int, piece: Piece) -> None:
        """
        Trigger hard drop effects.
        
        Args:
            x: Grid X position
            y: Grid Y position  
            piece: The piece that dropped
        """
        color = self._palette.get(piece.piece_type, (255, 255, 255))
        visible_y = y - 4  # Adjust for hidden rows
        
        if visible_y >= 0:
            self._particles.emit_hard_drop(
                x, visible_y, self._cell_size,
                self._grid_x, piece.bounds, color
            )
        
        self._shake.trigger(0.15)
    
    def trigger_tspin(self, x: int, y: int, is_mini: bool = False) -> None:
        """
        Trigger T-Spin effects.
        
        Args:
            x: Grid X position
            y: Grid Y position
            is_mini: Whether it's a mini T-Spin
        """
        color = self._palette["T"]
        visible_y = y - 4
        
        if visible_y >= 0:
            self._particles.emit_tspin(
                x, visible_y, self._cell_size,
                self._grid_x, color
            )
        
        shake_intensity = 0.3 if is_mini else 0.5
        self._shake.trigger(shake_intensity)
    
    @property
    def particles(self) -> ParticleSystem:
        """Get the particle system."""
        return self._particles
    
    @property
    def grid_position(self) -> Tuple[int, int]:
        """Get grid position in pixels."""
        return self._grid_x, self._grid_y
