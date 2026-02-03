"""
Tetris piece definitions with rotation states.
"""

from typing import List, Tuple, Dict
from dataclasses import dataclass
from copy import deepcopy


# Piece shape definitions (4 rotation states each)
# Each shape is a list of (x, y) offsets from the piece origin
# Rotation states: 0=spawn, 1=CW, 2=180, 3=CCW

PIECE_SHAPES: Dict[str, List[List[Tuple[int, int]]]] = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],  # 0 - spawn
        [(2, 0), (2, 1), (2, 2), (2, 3)],  # 1 - CW
        [(0, 2), (1, 2), (2, 2), (3, 2)],  # 2 - 180
        [(1, 0), (1, 1), (1, 2), (1, 3)],  # 3 - CCW
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],  # O piece doesn't rotate
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],  # 0 - spawn
        [(1, 0), (1, 1), (2, 1), (1, 2)],  # 1 - CW
        [(0, 1), (1, 1), (2, 1), (1, 2)],  # 2 - 180
        [(1, 0), (0, 1), (1, 1), (1, 2)],  # 3 - CCW
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],  # 0 - spawn
        [(1, 0), (1, 1), (2, 1), (2, 2)],  # 1 - CW
        [(1, 1), (2, 1), (0, 2), (1, 2)],  # 2 - 180
        [(0, 0), (0, 1), (1, 1), (1, 2)],  # 3 - CCW
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],  # 0 - spawn
        [(2, 0), (1, 1), (2, 1), (1, 2)],  # 1 - CW
        [(0, 1), (1, 1), (1, 2), (2, 2)],  # 2 - 180
        [(1, 0), (0, 1), (1, 1), (0, 2)],  # 3 - CCW
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],  # 0 - spawn
        [(1, 0), (2, 0), (1, 1), (1, 2)],  # 1 - CW
        [(0, 1), (1, 1), (2, 1), (2, 2)],  # 2 - 180
        [(1, 0), (1, 1), (0, 2), (1, 2)],  # 3 - CCW
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],  # 0 - spawn
        [(1, 0), (1, 1), (1, 2), (2, 2)],  # 1 - CW
        [(0, 1), (1, 1), (2, 1), (0, 2)],  # 2 - 180
        [(0, 0), (1, 0), (1, 1), (1, 2)],  # 3 - CCW
    ],
}

PIECE_NAMES = ["I", "O", "T", "S", "Z", "J", "L"]

# Bounding box sizes for each piece type
PIECE_BOUNDS = {
    "I": 4,
    "O": 3,
    "T": 3,
    "S": 3,
    "Z": 3,
    "J": 3,
    "L": 3,
}


@dataclass
class Piece:
    """
    Represents an active Tetris piece.
    """
    piece_type: str
    x: int  # Grid position (left edge of bounding box)
    y: int  # Grid position (top edge of bounding box)
    rotation: int  # 0-3
    
    def __post_init__(self):
        if self.piece_type not in PIECE_NAMES:
            raise ValueError(f"Invalid piece type: {self.piece_type}")
        self.rotation = self.rotation % 4
    
    def get_cells(self) -> List[Tuple[int, int]]:
        """
        Get the absolute grid positions of all cells in this piece.
        """
        shape = PIECE_SHAPES[self.piece_type][self.rotation]
        return [(self.x + dx, self.y + dy) for dx, dy in shape]
    
    def get_local_cells(self) -> List[Tuple[int, int]]:
        """
        Get the local positions of cells (relative to piece origin).
        """
        return list(PIECE_SHAPES[self.piece_type][self.rotation])
    
    def copy(self) -> 'Piece':
        """Create a copy of this piece."""
        return Piece(self.piece_type, self.x, self.y, self.rotation)
    
    @property
    def bounds(self) -> int:
        """Get the bounding box size for this piece type."""
        return PIECE_BOUNDS[self.piece_type]


# Pre-built piece templates for spawning
PIECES: Dict[str, Piece] = {
    name: Piece(name, 3, 0, 0) for name in PIECE_NAMES
}


def create_piece(piece_type: str, x: int = 3, y: int = 0) -> Piece:
    """
    Create a new piece at the specified position.
    
    Args:
        piece_type: One of I, O, T, S, Z, J, L
        x: Starting X position (default: 3 for center spawn)
        y: Starting Y position (default: 0)
    
    Returns:
        New Piece instance
    """
    return Piece(piece_type, x, y, 0)
