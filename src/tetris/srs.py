"""
Super Rotation System (SRS) implementation.
Handles wall kicks for all piece types including I-piece.
"""

from typing import List, Tuple, Optional
from .pieces import Piece, PIECE_SHAPES


# Wall kick data for J, L, S, T, Z pieces
# Format: (from_rotation, to_rotation): [(offset_x, offset_y), ...]
WALL_KICKS_JLSTZ: dict = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],   # 0 -> R (CW)
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],     # R -> 0 (CCW)
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],     # R -> 2 (CW)
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],   # 2 -> R (CCW)
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],      # 2 -> L (CW)
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],  # L -> 2 (CCW)
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],  # L -> 0 (CW)
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],      # 0 -> L (CCW)
}

# Wall kick data for I piece (different from others)
WALL_KICKS_I: dict = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],    # 0 -> R
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],    # R -> 0
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],    # R -> 2
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],    # 2 -> R
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],    # 2 -> L
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],    # L -> 2
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],    # L -> 0
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],    # 0 -> L
}

# 180 rotation kicks (for optional 180 rotation)
WALL_KICKS_180_JLSTZ: dict = {
    (0, 2): [(0, 0), (0, -1), (1, -1), (-1, -1), (1, 0), (-1, 0)],
    (2, 0): [(0, 0), (0, 1), (-1, 1), (1, 1), (-1, 0), (1, 0)],
    (1, 3): [(0, 0), (1, 0), (1, -2), (1, -1), (0, -2), (0, -1)],
    (3, 1): [(0, 0), (-1, 0), (-1, -2), (-1, -1), (0, -2), (0, -1)],
}

WALL_KICKS_180_I: dict = {
    (0, 2): [(0, 0), (0, -1)],
    (2, 0): [(0, 0), (0, 1)],
    (1, 3): [(0, 0), (1, 0)],
    (3, 1): [(0, 0), (-1, 0)],
}


class SRS:
    """
    Super Rotation System implementation.
    Handles rotation and wall kicks for all piece types.
    """
    
    @staticmethod
    def get_wall_kicks(piece_type: str, from_rot: int, to_rot: int) -> List[Tuple[int, int]]:
        """
        Get wall kick offsets for a rotation.
        
        Args:
            piece_type: Type of piece (I, O, T, etc.)
            from_rot: Starting rotation state (0-3)
            to_rot: Target rotation state (0-3)
        
        Returns:
            List of (x, y) kick offsets to try
        """
        if piece_type == "O":
            return [(0, 0)]  # O piece doesn't need kicks
        
        # Normalize rotation states
        from_rot = from_rot % 4
        to_rot = to_rot % 4
        
        key = (from_rot, to_rot)
        
        # Check if this is a 180 rotation
        if abs(from_rot - to_rot) == 2 or (from_rot == 3 and to_rot == 1) or (from_rot == 1 and to_rot == 3):
            if piece_type == "I":
                return WALL_KICKS_180_I.get(key, [(0, 0)])
            else:
                return WALL_KICKS_180_JLSTZ.get(key, [(0, 0)])
        
        # Regular rotation
        if piece_type == "I":
            return WALL_KICKS_I.get(key, [(0, 0)])
        else:
            return WALL_KICKS_JLSTZ.get(key, [(0, 0)])
    
    @staticmethod
    def rotate_cw(piece: Piece) -> int:
        """Get the clockwise rotation state."""
        return (piece.rotation + 1) % 4
    
    @staticmethod
    def rotate_ccw(piece: Piece) -> int:
        """Get the counter-clockwise rotation state."""
        return (piece.rotation + 3) % 4
    
    @staticmethod
    def rotate_180(piece: Piece) -> int:
        """Get the 180 rotation state."""
        return (piece.rotation + 2) % 4
    
    @staticmethod
    def try_rotation(
        piece: Piece,
        target_rotation: int,
        collision_check: callable
    ) -> Optional[Tuple[int, int, int]]:
        """
        Try to rotate a piece with wall kicks.
        
        Args:
            piece: The piece to rotate
            target_rotation: Target rotation state
            collision_check: Function(x, y, rotation) -> bool, returns True if collision
        
        Returns:
            (new_x, new_y, kick_index) if successful, None if rotation fails
        """
        kicks = SRS.get_wall_kicks(piece.piece_type, piece.rotation, target_rotation)
        
        for kick_index, (kick_x, kick_y) in enumerate(kicks):
            new_x = piece.x + kick_x
            new_y = piece.y - kick_y  # Y is inverted in SRS data
            
            if not collision_check(new_x, new_y, target_rotation):
                return (new_x, new_y, kick_index)
        
        return None


# T-Spin detection corners
# For each rotation state, the positions of the 4 corners around the T center
T_CORNERS = {
    0: [(-1, -1), (1, -1), (-1, 1), (1, 1)],  # Spawn state
    1: [(0, -1), (0, 1), (-1, -1), (-1, 1)],  # CW
    2: [(-1, -1), (1, -1), (-1, 1), (1, 1)],  # 180
    3: [(0, -1), (0, 1), (1, -1), (1, 1)],    # CCW
}

# Front corners for each rotation (the two corners "in front" of the T)
T_FRONT_CORNERS = {
    0: [(-1, -1), (1, -1)],   # Pointing up
    1: [(1, -1), (1, 1)],     # Pointing right
    2: [(-1, 1), (1, 1)],     # Pointing down
    3: [(-1, -1), (-1, 1)],   # Pointing left
}


def detect_tspin(piece: Piece, board_check: callable, kick_index: int) -> str:
    """
    Detect if a T piece placement is a T-Spin.
    
    Args:
        piece: The T piece that was just placed
        board_check: Function(x, y) -> bool, returns True if cell is occupied/wall
        kick_index: The wall kick index used (0 = no kick)
    
    Returns:
        "none", "mini", or "full"
    """
    if piece.piece_type != "T":
        return "none"
    
    # Get the center of the T (in the T-shape, the center is at offset (1,1) for spawn)
    # We need to find the actual center based on rotation
    center_offsets = {
        0: (1, 1),
        1: (1, 1),
        2: (1, 1),
        3: (1, 1),
    }
    
    cx, cy = center_offsets[piece.rotation]
    center_x = piece.x + cx
    center_y = piece.y + cy
    
    # Count occupied corners
    corners_filled = 0
    front_corners_filled = 0
    
    # Check all 4 corners
    all_corners = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    front_corners = T_FRONT_CORNERS[piece.rotation]
    
    for dx, dy in all_corners:
        if board_check(center_x + dx, center_y + dy):
            corners_filled += 1
            if (dx, dy) in front_corners:
                front_corners_filled += 1
    
    # T-Spin detection rules:
    # - At least 3 corners must be filled
    # - If both front corners are filled, it's a full T-Spin
    # - Otherwise, it's a mini T-Spin (unless it used kick 4, making it full)
    
    if corners_filled >= 3:
        if front_corners_filled == 2:
            return "full"
        elif kick_index == 4:  # Last kick (the "twist" kick)
            return "full"
        else:
            return "mini"
    
    return "none"
