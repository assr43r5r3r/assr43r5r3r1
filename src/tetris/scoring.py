"""
Scoring system with combo, back-to-back, and T-Spin detection.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScoreEvent:
    """Represents a scoring event."""
    lines_cleared: int = 0
    is_tspin: bool = False
    is_tspin_mini: bool = False
    is_perfect_clear: bool = False
    is_hard_drop: bool = False
    drop_distance: int = 0
    combo: int = 0
    is_back_to_back: bool = False
    level: int = 1


class Scoring:
    """
    Tetris scoring system.
    
    Implements modern guideline scoring with:
    - Line clears (single, double, triple, tetris)
    - T-Spins (mini and full)
    - Combos
    - Back-to-back bonuses
    - Perfect clears
    """
    
    # Base scores for line clears - simplified: 10 points per row
    BASE_SCORES = {
        0: 0,
        1: 10,    # Single - 10 pts
        2: 20,    # Double - 20 pts
        3: 30,    # Triple - 30 pts
        4: 40,    # Tetris - 40 pts
    }
    
    # T-Spin scores - bonus on top of line clears
    TSPIN_SCORES = {
        (False, 0): 0,     # T-Spin no lines
        (False, 1): 10,    # T-Spin Single bonus
        (False, 2): 20,    # T-Spin Double bonus
        (False, 3): 30,    # T-Spin Triple bonus
        (True, 0): 0,      # T-Spin Mini no lines
        (True, 1): 5,      # T-Spin Mini Single bonus
        (True, 2): 10,     # T-Spin Mini Double bonus
    }
    
    # Perfect clear bonus
    PERFECT_CLEAR_BONUS = 50
    
    # Back-to-back multiplier
    B2B_MULTIPLIER = 1.5
    
    # Combo bonus per combo count
    COMBO_BONUS = 5
    
    def __init__(self):
        self._score = 0
        self._lines_cleared = 0
        self._level = 1
        self._combo = -1  # -1 so first clear gives combo 0
        self._back_to_back = False
        self._last_was_difficult = False
        
        # Stats
        self._singles = 0
        self._doubles = 0
        self._triples = 0
        self._tetrises = 0
        self._tspins = 0
        self._tspin_minis = 0
        self._perfect_clears = 0
        self._max_combo = 0
        self._back_to_back_count = 0
    
    def calculate_score(self, event: ScoreEvent) -> int:
        """
        Calculate and add score for a scoring event.
        
        Args:
            event: The scoring event
        
        Returns:
            Points awarded for this event
        """
        points = 0
        
        # Handle T-Spin - adds bonus to line clear points
        if event.is_tspin or event.is_tspin_mini:
            key = (event.is_tspin_mini, event.lines_cleared)
            tspin_bonus = self.TSPIN_SCORES.get(key, 0)
            # Also add the regular line clear points
            points = self.BASE_SCORES.get(event.lines_cleared, 0) + tspin_bonus
            
            # Update stats
            if event.is_tspin_mini:
                self._tspin_minis += 1
            else:
                self._tspins += 1
            
            is_difficult = True
        elif event.lines_cleared > 0:
            # Regular line clear - simple 10 pts per row
            points = self.BASE_SCORES.get(event.lines_cleared, 0)
            is_difficult = (event.lines_cleared == 4)  # Tetris is difficult
            
            # Update stats
            if event.lines_cleared == 1:
                self._singles += 1
            elif event.lines_cleared == 2:
                self._doubles += 1
            elif event.lines_cleared == 3:
                self._triples += 1
            elif event.lines_cleared == 4:
                self._tetrises += 1
        else:
            is_difficult = False
        
        # Back-to-back bonus
        if event.lines_cleared > 0:
            if is_difficult and self._last_was_difficult:
                points = int(points * self.B2B_MULTIPLIER)
                self._back_to_back = True
                self._back_to_back_count += 1
            else:
                self._back_to_back = False
            
            self._last_was_difficult = is_difficult
            
            # Combo bonus (no level multiplier)
            self._combo += 1
            if self._combo > 0:
                points += self.COMBO_BONUS * self._combo
            self._max_combo = max(self._max_combo, self._combo)
        else:
            # No lines cleared, reset combo
            self._combo = -1
        
        # Perfect clear bonus
        if event.is_perfect_clear:
            points += self.PERFECT_CLEAR_BONUS
            self._perfect_clears += 1
        
        # No hard drop or soft drop points - only row clears give points
        
        self._score += points
        self._lines_cleared += event.lines_cleared
        
        return points
    
    def add_soft_drop_points(self, cells: int) -> None:
        """Soft drop no longer gives points - score only from row clears."""
        pass  # No points for soft drops
    
    def update_level(self, lines_per_level: int = 10) -> bool:
        """
        Update level based on lines cleared.
        
        Returns:
            True if level increased
        """
        new_level = (self._lines_cleared // lines_per_level) + 1
        if new_level > self._level:
            self._level = new_level
            return True
        return False
    
    def reset(self) -> None:
        """Reset all scoring data."""
        self._score = 0
        self._lines_cleared = 0
        self._level = 1
        self._combo = -1
        self._back_to_back = False
        self._last_was_difficult = False
        
        self._singles = 0
        self._doubles = 0
        self._triples = 0
        self._tetrises = 0
        self._tspins = 0
        self._tspin_minis = 0
        self._perfect_clears = 0
        self._max_combo = 0
        self._back_to_back_count = 0
    
    @property
    def score(self) -> int:
        """Current score."""
        return self._score
    
    @property
    def lines(self) -> int:
        """Total lines cleared."""
        return self._lines_cleared
    
    @property
    def level(self) -> int:
        """Current level."""
        return self._level
    
    @level.setter
    def level(self, value: int) -> None:
        """Set level directly."""
        self._level = max(1, value)
    
    @property
    def combo(self) -> int:
        """Current combo count."""
        return max(0, self._combo)
    
    @property
    def is_back_to_back(self) -> bool:
        """Whether last clear was back-to-back."""
        return self._back_to_back
    
    def get_stats(self) -> dict:
        """Get all statistics."""
        return {
            "score": self._score,
            "lines": self._lines_cleared,
            "level": self._level,
            "singles": self._singles,
            "doubles": self._doubles,
            "triples": self._triples,
            "tetrises": self._tetrises,
            "tspins": self._tspins,
            "tspin_minis": self._tspin_minis,
            "perfect_clears": self._perfect_clears,
            "max_combo": self._max_combo,
            "back_to_back_count": self._back_to_back_count,
        }
