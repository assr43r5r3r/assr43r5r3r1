"""
7-Bag randomizer for deterministic piece generation.
"""

import random
from typing import List, Optional
from .pieces import PIECE_NAMES


class Bag:
    """
    7-Bag randomizer implementation.
    
    Generates pieces in sets of 7 (one of each type), shuffled randomly.
    Supports deterministic replay with seed.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the bag.
        
        Args:
            seed: Random seed for deterministic generation. None for random.
        """
        self._seed = seed
        self._rng = random.Random(seed)
        self._bag: List[str] = []
        self._history: List[str] = []
        
        # Pre-fill with first bag
        self._refill()
    
    def _refill(self) -> None:
        """Fill the bag with a new shuffled set of 7 pieces."""
        new_pieces = list(PIECE_NAMES)
        self._rng.shuffle(new_pieces)
        self._bag.extend(new_pieces)
    
    def next(self) -> str:
        """
        Get the next piece from the bag.
        
        Returns:
            Piece type string (I, O, T, etc.)
        """
        if len(self._bag) < 7:
            self._refill()
        
        piece = self._bag.pop(0)
        self._history.append(piece)
        return piece
    
    def peek(self, count: int = 6) -> List[str]:
        """
        Preview upcoming pieces without consuming them.
        
        Args:
            count: Number of pieces to preview
        
        Returns:
            List of upcoming piece types
        """
        while len(self._bag) < count:
            self._refill()
        
        return self._bag[:count]
    
    def reset(self, seed: Optional[int] = None) -> None:
        """
        Reset the bag with a new seed.
        
        Args:
            seed: New random seed, or None for random
        """
        self._seed = seed
        self._rng = random.Random(seed)
        self._bag.clear()
        self._history.clear()
        self._refill()
    
    @property
    def seed(self) -> Optional[int]:
        """Get the current seed."""
        return self._seed
    
    @property
    def history(self) -> List[str]:
        """Get the history of all pieces generated."""
        return list(self._history)
    
    @property
    def piece_count(self) -> int:
        """Get the total number of pieces generated."""
        return len(self._history)
    
    def get_state(self) -> dict:
        """
        Get serializable state for replay.
        
        Returns:
            Dictionary with bag state
        """
        return {
            "seed": self._seed,
            "history_count": len(self._history),
            "bag": list(self._bag),
        }
    
    @classmethod
    def from_state(cls, state: dict) -> 'Bag':
        """
        Restore bag from state.
        
        Args:
            state: State dictionary from get_state()
        
        Returns:
            New Bag instance
        """
        bag = cls(state["seed"])
        # Fast-forward to same state
        for _ in range(state["history_count"]):
            bag.next()
        return bag
