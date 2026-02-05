"""
Tests for SRS rotation system.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tetris.pieces import Piece, PIECE_SHAPES
from src.tetris.srs import SRS, detect_tspin
from src.tetris.board import Board


class TestSRSRotation(unittest.TestCase):
    """Test SRS rotation states."""
    
    def test_i_piece_rotation_states(self):
        """Test I piece has correct rotation states."""
        piece = Piece("I", 0, 0, 0)
        
        # Spawn state (horizontal)
        cells = piece.get_local_cells()
        self.assertEqual(len(cells), 4)
        
        # All cells should be on same row
        y_values = [y for x, y in cells]
        self.assertEqual(len(set(y_values)), 1)
    
    def test_o_piece_no_rotation(self):
        """Test O piece doesn't change on rotation."""
        piece = Piece("O", 3, 3, 0)
        cells_0 = piece.get_local_cells()
        
        piece.rotation = 1
        cells_1 = piece.get_local_cells()
        
        piece.rotation = 2
        cells_2 = piece.get_local_cells()
        
        piece.rotation = 3
        cells_3 = piece.get_local_cells()
        
        # All rotations should be the same
        self.assertEqual(sorted(cells_0), sorted(cells_1))
        self.assertEqual(sorted(cells_1), sorted(cells_2))
        self.assertEqual(sorted(cells_2), sorted(cells_3))
    
    def test_t_piece_rotation_states(self):
        """Test T piece rotation states are different."""
        rotations = []
        for r in range(4):
            piece = Piece("T", 0, 0, r)
            rotations.append(frozenset(piece.get_local_cells()))
        
        # T piece should have 4 distinct rotation states
        self.assertEqual(len(set(rotations)), 4)
    
    def test_rotation_functions(self):
        """Test rotation helper functions."""
        piece = Piece("T", 3, 3, 0)
        
        self.assertEqual(SRS.rotate_cw(piece), 1)
        self.assertEqual(SRS.rotate_ccw(piece), 3)
        self.assertEqual(SRS.rotate_180(piece), 2)
        
        piece.rotation = 3
        self.assertEqual(SRS.rotate_cw(piece), 0)
        self.assertEqual(SRS.rotate_ccw(piece), 2)


class TestSRSWallKicks(unittest.TestCase):
    """Test SRS wall kick data."""
    
    def test_wall_kicks_exist(self):
        """Test wall kick data exists for all rotations."""
        # JLSTZ pieces
        for piece_type in ["J", "L", "S", "T", "Z"]:
            for from_rot in range(4):
                to_rot = (from_rot + 1) % 4  # CW
                kicks = SRS.get_wall_kicks(piece_type, from_rot, to_rot)
                self.assertEqual(len(kicks), 5, f"Expected 5 kicks for {piece_type}")
    
    def test_i_piece_wall_kicks(self):
        """Test I piece has different wall kicks."""
        i_kicks = SRS.get_wall_kicks("I", 0, 1)
        t_kicks = SRS.get_wall_kicks("T", 0, 1)
        
        # I piece kicks should be different from other pieces
        self.assertNotEqual(i_kicks, t_kicks)
    
    def test_o_piece_no_kicks(self):
        """Test O piece has only (0,0) kick."""
        kicks = SRS.get_wall_kicks("O", 0, 1)
        self.assertEqual(kicks, [(0, 0)])
    
    def test_wall_kick_success(self):
        """Test wall kick allows rotation against wall."""
        board = Board()
        
        # Place I piece against left wall
        piece = Piece("I", -1, 10, 0)
        
        # Without kicks, rotation would fail
        # With kicks, it should succeed
        def collision_check(x, y, rot):
            return board.check_collision(x, y, rot, piece.piece_type)
        
        result = SRS.try_rotation(piece, 1, collision_check)
        
        # Should find a valid position with kicks
        self.assertIsNotNone(result)
        new_x, new_y, kick_index = result
        
        # Verify the new position is valid
        self.assertFalse(board.check_collision(new_x, new_y, 1, piece.piece_type))


class TestTSpinDetection(unittest.TestCase):
    """Test T-Spin detection."""
    
    def test_no_tspin_in_open(self):
        """Test no T-Spin detected in open space."""
        board = Board()
        piece = Piece("T", 4, 10, 0)
        
        result = detect_tspin(piece, board.is_cell_filled, 0)
        self.assertEqual(result, "none")
    
    def test_non_t_piece(self):
        """Test non-T pieces return 'none'."""
        board = Board()
        piece = Piece("I", 4, 10, 0)
        
        result = detect_tspin(piece, board.is_cell_filled, 0)
        self.assertEqual(result, "none")
    
    def test_tspin_with_filled_corners(self):
        """Test T-Spin with corners filled."""
        board = Board()
        
        # Set up a T-Spin pocket
        # Fill the corners around where T will be placed
        # T piece center at (4, 10), we need 3 corners filled
        board.set_cell(3, 9, "X")   # Top-left corner
        board.set_cell(5, 9, "X")   # Top-right corner  
        board.set_cell(3, 11, "X")  # Bottom-left corner
        
        piece = Piece("T", 3, 9, 0)
        
        result = detect_tspin(piece, board.is_cell_filled, 0)
        # With 3 corners and 2 front corners, should be full
        self.assertIn(result, ["full", "mini"])


if __name__ == "__main__":
    unittest.main()
