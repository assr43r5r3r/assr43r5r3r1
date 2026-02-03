"""
Tests for 7-bag randomizer.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tetris.bag import Bag
from src.tetris.pieces import PIECE_NAMES


class TestBag(unittest.TestCase):
    """Test 7-bag randomizer."""
    
    def test_bag_contains_all_pieces(self):
        """Test that first 7 pieces contain one of each."""
        bag = Bag(seed=12345)
        
        pieces = [bag.next() for _ in range(7)]
        
        # Should have exactly one of each piece type
        self.assertEqual(sorted(pieces), sorted(PIECE_NAMES))
    
    def test_deterministic_with_seed(self):
        """Test same seed produces same sequence."""
        seed = 42
        
        bag1 = Bag(seed=seed)
        sequence1 = [bag1.next() for _ in range(21)]
        
        bag2 = Bag(seed=seed)
        sequence2 = [bag2.next() for _ in range(21)]
        
        self.assertEqual(sequence1, sequence2)
    
    def test_different_seeds_different_sequences(self):
        """Test different seeds produce different sequences."""
        bag1 = Bag(seed=1)
        sequence1 = [bag1.next() for _ in range(7)]
        
        bag2 = Bag(seed=2)
        sequence2 = [bag2.next() for _ in range(7)]
        
        # Very unlikely to be the same
        self.assertNotEqual(sequence1, sequence2)
    
    def test_peek_does_not_consume(self):
        """Test peeking doesn't remove pieces from bag."""
        bag = Bag(seed=100)
        
        peeked = bag.peek(6)
        
        # Get next pieces
        actual = [bag.next() for _ in range(6)]
        
        self.assertEqual(peeked, actual)
    
    def test_peek_returns_correct_count(self):
        """Test peek returns requested number of pieces."""
        bag = Bag(seed=100)
        
        for count in [1, 3, 6, 10]:
            peeked = bag.peek(count)
            self.assertEqual(len(peeked), count)
    
    def test_history_tracking(self):
        """Test history tracks all generated pieces."""
        bag = Bag(seed=100)
        
        pieces = [bag.next() for _ in range(14)]
        
        self.assertEqual(bag.history, pieces)
        self.assertEqual(bag.piece_count, 14)
    
    def test_reset_clears_state(self):
        """Test reset clears bag state."""
        bag = Bag(seed=100)
        
        # Generate some pieces
        for _ in range(10):
            bag.next()
        
        # Reset with new seed
        bag.reset(seed=200)
        
        self.assertEqual(bag.piece_count, 0)
        self.assertEqual(len(bag.history), 0)
    
    def test_reset_with_same_seed(self):
        """Test reset with same seed gives same sequence."""
        seed = 12345
        bag = Bag(seed=seed)
        
        first_sequence = [bag.next() for _ in range(14)]
        
        bag.reset(seed=seed)
        
        second_sequence = [bag.next() for _ in range(14)]
        
        self.assertEqual(first_sequence, second_sequence)
    
    def test_multiple_bags_complete(self):
        """Test that multiple bags each have all pieces."""
        bag = Bag(seed=100)
        
        # Get 3 complete bags worth of pieces
        for bag_num in range(3):
            pieces = [bag.next() for _ in range(7)]
            self.assertEqual(
                sorted(pieces), 
                sorted(PIECE_NAMES),
                f"Bag {bag_num + 1} should have all pieces"
            )


class TestBagState(unittest.TestCase):
    """Test bag state serialization."""
    
    def test_get_state(self):
        """Test getting bag state."""
        bag = Bag(seed=100)
        
        for _ in range(5):
            bag.next()
        
        state = bag.get_state()
        
        self.assertEqual(state["seed"], 100)
        self.assertEqual(state["history_count"], 5)
        self.assertIn("bag", state)
    
    def test_from_state_restoration(self):
        """Test restoring bag from state produces same next pieces."""
        bag1 = Bag(seed=100)
        
        # Generate some pieces
        for _ in range(10):
            bag1.next()
        
        # Get state and next pieces from original
        state = bag1.get_state()
        next_pieces_1 = [bag1.next() for _ in range(7)]
        
        # Restore from state
        bag2 = Bag.from_state(state)
        next_pieces_2 = [bag2.next() for _ in range(7)]
        
        self.assertEqual(next_pieces_1, next_pieces_2)


if __name__ == "__main__":
    unittest.main()
