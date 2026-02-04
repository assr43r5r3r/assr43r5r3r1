"""
Central save manager that coordinates all save systems.
"""

from typing import Optional
import os

from .profile import PlayerProfile, ProfileManager
from .leaderboard import Leaderboard


class SaveManager:
    """
    Central manager for all save/load operations.
    """
    
    _instance: Optional['SaveManager'] = None
    
    def __init__(self, save_dir: str = "saves"):
        """
        Initialize save manager.
        
        Args:
            save_dir: Base directory for all save data
        """
        self._save_dir = save_dir
        self._profile_manager = ProfileManager(save_dir)
        self._leaderboard = Leaderboard(save_dir)
        
        SaveManager._instance = self
    
    @classmethod
    def get_instance(cls) -> 'SaveManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def profiles(self) -> ProfileManager:
        """Get profile manager."""
        return self._profile_manager
    
    @property
    def leaderboard(self) -> Leaderboard:
        """Get leaderboard."""
        return self._leaderboard
    
    @property
    def current_player(self) -> Optional[PlayerProfile]:
        """Get current player profile."""
        return self._profile_manager.current_profile
    
    def record_game(
        self,
        score: int,
        stage: int,
        lines: int,
        time_played: float
    ) -> int:
        """
        Record a completed game.
        
        Args:
            score: Final score
            stage: Final stage reached
            lines: Lines cleared
            time_played: Time played in seconds
            
        Returns:
            Leaderboard position (1-indexed), or -1 if no profile
        """
        profile = self._profile_manager.current_profile
        if not profile:
            return -1
        
        # Update profile stats
        profile.update_stats(score, stage, lines, time_played)
        self._profile_manager.update_profile(profile)
        
        # Add to leaderboard
        position = self._leaderboard.add_entry(
            player_name=profile.name,
            player_id=profile.id,
            score=score,
            stage=stage,
            lines=lines,
            time_played=time_played
        )
        
        return position
    
    def quick_create_profile(self, name: str) -> PlayerProfile:
        """
        Quick create a new profile and set as current.
        
        Args:
            name: Player name
            
        Returns:
            New profile
        """
        profile = self._profile_manager.create_profile(name)
        self._profile_manager.set_current_profile(profile.id)
        return profile
