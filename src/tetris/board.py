"""
Tetris game board logic.
"""

from typing import List, Tuple, Optional, Set
from .pieces import Piece, PIECE_SHAPES


class Board:
    """
    The Tetris playfield (board).
    
    Handles collision detection, line clearing, and cell management.
    The board is 10 wide × 24 tall (20 visible + 4 hidden spawn rows).
    """
    
    def __init__(self, width: int = 10, height: int = 20, hidden_rows: int = 4):
        """
        Initialize the board.
        
        Args:
            width: Board width in cells
            height: Visible board height
            hidden_rows: Number of hidden rows above visible area
        """
        self.width = width
        self.height = height
        self.hidden_rows = hidden_rows
        self.total_height = height + hidden_rows
        
        # Grid stores piece types or None
        # Row 0 is the top (hidden area), row total_height-1 is the bottom
        self._grid: List[List[Optional[str]]] = [
            [None for _ in range(width)] for _ in range(self.total_height)
        ]
    
    def is_valid_position(self, piece: Piece, x: int = None, y: int = None, 
                          rotation: int = None) -> bool:
        """
        Check if a piece can be placed at the given position.
        
        Args:
            piece: The piece to check
            x: X position (uses piece.x if None)
            y: Y position (uses piece.y if None)
            rotation: Rotation state (uses piece.rotation if None)
        
        Returns:
            True if position is valid
        """
        test_x = x if x is not None else piece.x
        test_y = y if y is not None else piece.y
        test_rot = rotation if rotation is not None else piece.rotation
        
        shape = PIECE_SHAPES[piece.piece_type][test_rot]
        
        for dx, dy in shape:
            cell_x = test_x + dx
            cell_y = test_y + dy
            
            # Check bounds
            if cell_x < 0 or cell_x >= self.width:
                return False
            if cell_y < 0 or cell_y >= self.total_height:
                return False
            
            # Check collision with placed pieces
            if self._grid[cell_y][cell_x] is not None:
                return False
        
        return True
    
    def check_collision(self, x: int, y: int, rotation: int, piece_type: str) -> bool:
        """
        Check if there's a collision at the given position.
        
        Returns:
            True if there IS a collision
        """
        shape = PIECE_SHAPES[piece_type][rotation]
        
        for dx, dy in shape:
            cell_x = x + dx
            cell_y = y + dy
            
            if cell_x < 0 or cell_x >= self.width:
                return True
            if cell_y < 0 or cell_y >= self.total_height:
                return True
            if self._grid[cell_y][cell_x] is not None:
                return True
        
        return False
    
    def is_cell_filled(self, x: int, y: int) -> bool:
        """
        Check if a cell is filled or out of bounds.
        
        Returns:
            True if cell is filled or out of bounds
        """
        if x < 0 or x >= self.width:
            return True
        if y < 0 or y >= self.total_height:
            return True
        return self._grid[y][x] is not None
    
    def lock_piece(self, piece: Piece) -> None:
        """
        Lock a piece into the board.
        
        Args:
            piece: The piece to lock
        """
        for cell_x, cell_y in piece.get_cells():
            if 0 <= cell_x < self.width and 0 <= cell_y < self.total_height:
                self._grid[cell_y][cell_x] = piece.piece_type
    
    def get_drop_distance(self, piece: Piece) -> int:
        """
        Calculate how far a piece can drop.
        
        Returns:
            Number of rows the piece can drop
        """
        distance = 0
        while self.is_valid_position(piece, y=piece.y + distance + 1):
            distance += 1
        return distance
    
    def get_ghost_position(self, piece: Piece) -> int:
        """
        Get the Y position where the ghost piece should appear.
        
        Returns:
            Y position for ghost piece
        """
        return piece.y + self.get_drop_distance(piece)
    
    def clear_lines(self) -> Tuple[int, List[int]]:
        """
        Clear any complete lines.
        
        Returns:
            (number of lines cleared, list of cleared row indices)
        """
        cleared_rows = []
        
        # Find complete rows
        for y in range(self.total_height):
            if all(self._grid[y][x] is not None for x in range(self.width)):
                cleared_rows.append(y)
        
        if not cleared_rows:
            return 0, []
        
        # Remove cleared rows and add empty rows at top
        for y in sorted(cleared_rows, reverse=True):
            del self._grid[y]
        
        for _ in range(len(cleared_rows)):
            self._grid.insert(0, [None for _ in range(self.width)])
        
        return len(cleared_rows), cleared_rows
    
    def is_empty(self) -> bool:
        """Check if the board is completely empty (for perfect clear detection)."""
        return all(
            self._grid[y][x] is None
            for y in range(self.total_height)
            for x in range(self.width)
        )
    
    def is_topped_out(self, piece: Piece) -> bool:
        """
        Check if a piece spawn would cause a top-out.
        
        Returns:
            True if the piece cannot spawn (game over condition)
        """
        # Check if any part of the piece overlaps with placed cells in spawn position
        return not self.is_valid_position(piece)
    
    def get_cell(self, x: int, y: int) -> Optional[str]:
        """Get the piece type at a cell, or None if empty."""
        if 0 <= x < self.width and 0 <= y < self.total_height:
            return self._grid[y][x]
        return None
    
    def set_cell(self, x: int, y: int, piece_type: Optional[str]) -> None:
        """Set a cell to a piece type or None."""
        if 0 <= x < self.width and 0 <= y < self.total_height:
            self._grid[y][x] = piece_type
    
    def get_column_height(self, column: int) -> int:
        """Get the height of pieces in a column."""
        for y in range(self.total_height):
            if self._grid[y][column] is not None:
                return self.total_height - y
        return 0
    
    def get_max_height(self) -> int:
        """Get the maximum stack height."""
        return max(self.get_column_height(x) for x in range(self.width))
    
    def reset(self) -> None:
        """Clear the entire board."""
        self._grid = [
            [None for _ in range(self.width)] for _ in range(self.total_height)
        ]
    
    def get_state(self) -> List[List[Optional[str]]]:
        """Get a copy of the grid state for serialization."""
        return [row.copy() for row in self._grid]
    
    def set_state(self, grid: List[List[Optional[str]]]) -> None:
        """Restore grid from state."""
        self._grid = [row.copy() for row in grid]
    
    def get_visible_grid(self) -> List[List[Optional[str]]]:
        """Get only the visible portion of the grid."""
        return [row.copy() for row in self._grid[self.hidden_rows:]]
