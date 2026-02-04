"""
Leaderboard system for tracking high scores.
"""

import json
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime


# Stage name mapping
STAGE_NAMES = {
    1: "Beginner", 2: "Novice", 3: "Amateur", 4: "Rookie", 5: "Starter",
    6: "Apprentice", 7: "Journeyman", 8: "Skilled", 9: "Adept", 10: "Expert",
    11: "Veteran", 12: "Elite", 13: "Master", 14: "Grandmaster", 15: "Champion",
    16: "Hero", 17: "Legend", 18: "Mythic", 19: "Divine", 20: "Celestial",
    21: "Cosmic", 22: "Transcendent", 23: "Eternal", 24: "Supreme", 25: "Ultimate",
}


@dataclass
class LeaderboardEntry:
    """A single leaderboard entry."""
    player_name: str
    player_id: str
    score: int
    stage: int
    lines: int
    time_played: float  # In seconds
    date: str = ""
    
    def __post_init__(self):
        if not self.date:
            self.date = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LeaderboardEntry':
        return cls(**data)
    
    @property
    def formatted_time(self) -> str:
        """Format time as MM:SS."""
        minutes = int(self.time_played // 60)
        seconds = int(self.time_played % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def stage_name(self) -> str:
        """Get human-readable stage name."""
        return STAGE_NAMES.get(self.stage, f"Stage {self.stage}")


class Leaderboard:
    """
    Manages the game leaderboard.
    """
    
    MAX_ENTRIES = 100  # Keep top 100 scores
    
    def __init__(self, save_dir: str = "saves"):
        """
        Initialize leaderboard.
        
        Args:
            save_dir: Directory for save files
        """
        self._save_dir = save_dir
        self._entries: List[LeaderboardEntry] = []
        self._file_path = os.path.join(save_dir, "leaderboard.json")
        
        self._ensure_save_dir()
        self._load()
    
    def _ensure_save_dir(self) -> None:
        """Create save directory if it doesn't exist."""
        os.makedirs(self._save_dir, exist_ok=True)
    
    def _load(self) -> None:
        """Load leaderboard from disk."""
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, 'r') as f:
                    data = json.load(f)
                    self._entries = [
                        LeaderboardEntry.from_dict(e) 
                        for e in data.get('entries', [])
                    ]
                    self._sort()
            except Exception as e:
                print(f"Error loading leaderboard: {e}")
    
    def _save(self) -> None:
        """Save leaderboard to disk."""
        self._ensure_save_dir()
        try:
            data = {
                'entries': [e.to_dict() for e in self._entries]
            }
            with open(self._file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
    
    def _sort(self) -> None:
        """Sort entries by score (descending)."""
        self._entries.sort(key=lambda e: e.score, reverse=True)
    
    def add_entry(
        self,
        player_name: str,
        player_id: str,
        score: int,
        stage: int,
        lines: int,
        time_played: float
    ) -> int:
        """
        Add a new leaderboard entry.
        
        Only keeps the best entry per player (by score).
        
        Args:
            player_name: Player name
            player_id: Player profile ID
            score: Final score
            stage: Final stage reached
            lines: Total lines cleared
            time_played: Time played in seconds
            
        Returns:
            Position in leaderboard (1-indexed), or -1 if not ranked
        """
        entry = LeaderboardEntry(
            player_name=player_name,
            player_id=player_id,
            score=score,
            stage=stage,
            lines=lines,
            time_played=time_played
        )
        
        # Remove any existing entry for this player with lower score
        self._entries = [
            e for e in self._entries 
            if e.player_id != player_id or e.score > score
        ]
        
        # Only add if this score isn't beaten by an existing entry
        existing_best = self.get_player_best(player_id)
        if existing_best is None or score > existing_best.score:
            # Remove the old best (if any) and add new one
            self._entries = [e for e in self._entries if e.player_id != player_id]
            self._entries.append(entry)
        
        self._sort()
        
        # Trim to max entries
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries = self._entries[:self.MAX_ENTRIES]
        
        self._save()
        
        # Find position
        for i, e in enumerate(self._entries):
            if e.player_id == player_id:
                return i + 1
        return -1
    
    def get_top(self, count: int = 10) -> List[LeaderboardEntry]:
        """Get top N entries."""
        return self._entries[:count]
    
    def get_rank(self, score: int) -> int:
        """
        Get what rank a score would achieve.
        
        Args:
            score: Score to check
            
        Returns:
            Rank (1-indexed)
        """
        for i, entry in enumerate(self._entries):
            if score > entry.score:
                return i + 1
        return len(self._entries) + 1
    
    def get_player_best(self, player_id: str) -> Optional[LeaderboardEntry]:
        """Get best entry for a player."""
        for entry in self._entries:
            if entry.player_id == player_id:
                return entry
        return None
    
    def get_player_entries(self, player_id: str, limit: int = 5) -> List[LeaderboardEntry]:
        """Get all entries for a player."""
        entries = [e for e in self._entries if e.player_id == player_id]
        return entries[:limit]
    
    def is_high_score(self, score: int) -> bool:
        """Check if score qualifies for leaderboard."""
        if len(self._entries) < self.MAX_ENTRIES:
            return True
        return score > self._entries[-1].score
    
    @property
    def entries(self) -> List[LeaderboardEntry]:
        """Get all entries."""
        return self._entries.copy()
    
    @property
    def count(self) -> int:
        """Get number of entries."""
        return len(self._entries)
