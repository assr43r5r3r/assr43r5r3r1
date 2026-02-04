"""
Player profile system for saving player data and avatars.
"""

import json
import os
import base64
import uuid
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class PlayerProfile:
    """
    Represents a player profile with their data.
    """
    id: str = ""
    name: str = "Player"
    avatar_path: Optional[str] = None  # Path to avatar image
    avatar_data: Optional[str] = None  # Base64 encoded avatar for portability
    high_score: int = 0
    highest_stage: int = 1
    total_lines: int = 0
    total_games: int = 0
    total_play_time: float = 0.0  # In seconds
    created_at: str = ""
    last_played: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_played:
            self.last_played = datetime.now().isoformat()
    
    def update_stats(self, score: int, stage: int, lines: int, play_time: float) -> None:
        """Update player statistics after a game."""
        self.high_score = max(self.high_score, score)
        self.highest_stage = max(self.highest_stage, stage)
        self.total_lines += lines
        self.total_games += 1
        self.total_play_time += play_time
        self.last_played = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerProfile':
        """Create from dictionary."""
        return cls(**data)
    
    def set_avatar_from_file(self, file_path: str) -> bool:
        """
        Load avatar from file and store as base64.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                self.avatar_data = base64.b64encode(data).decode('utf-8')
                self.avatar_path = file_path
            return True
        except Exception:
            return False
    
    def get_avatar_surface(self):
        """
        Get avatar as pygame surface.
        
        Returns:
            Pygame surface or None
        """
        if self.avatar_data:
            try:
                import pygame
                import io
                data = base64.b64decode(self.avatar_data)
                return pygame.image.load(io.BytesIO(data))
            except Exception:
                pass
        return None


class ProfileManager:
    """
    Manages player profiles and persistence.
    """
    
    def __init__(self, save_dir: str = "saves"):
        """
        Initialize profile manager.
        
        Args:
            save_dir: Directory for save files
        """
        self._save_dir = save_dir
        self._profiles: Dict[str, PlayerProfile] = {}
        self._current_profile: Optional[PlayerProfile] = None
        self._profiles_file = os.path.join(save_dir, "profiles.json")
        
        self._ensure_save_dir()
        self._load_profiles()
    
    def _ensure_save_dir(self) -> None:
        """Create save directory if it doesn't exist."""
        os.makedirs(self._save_dir, exist_ok=True)
    
    def _load_profiles(self) -> None:
        """Load all profiles from disk."""
        if os.path.exists(self._profiles_file):
            try:
                with open(self._profiles_file, 'r') as f:
                    data = json.load(f)
                    for profile_data in data.get('profiles', []):
                        profile = PlayerProfile.from_dict(profile_data)
                        self._profiles[profile.id] = profile
                    
                    # Load current profile
                    current_id = data.get('current_profile')
                    if current_id and current_id in self._profiles:
                        self._current_profile = self._profiles[current_id]
            except Exception as e:
                print(f"Error loading profiles: {e}")
    
    def _save_profiles(self) -> None:
        """Save all profiles to disk."""
        self._ensure_save_dir()
        try:
            data = {
                'profiles': [p.to_dict() for p in self._profiles.values()],
                'current_profile': self._current_profile.id if self._current_profile else None
            }
            with open(self._profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
    
    def create_profile(self, name: str, avatar_path: Optional[str] = None) -> PlayerProfile:
        """
        Create a new player profile.
        
        Args:
            name: Player name
            avatar_path: Optional path to avatar image
            
        Returns:
            New PlayerProfile
        """
        profile = PlayerProfile(name=name)
        if avatar_path:
            profile.set_avatar_from_file(avatar_path)
        
        self._profiles[profile.id] = profile
        self._save_profiles()
        return profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            if self._current_profile and self._current_profile.id == profile_id:
                self._current_profile = None
            self._save_profiles()
            return True
        return False
    
    def set_current_profile(self, profile_id: str) -> bool:
        """Set the current active profile."""
        if profile_id in self._profiles:
            self._current_profile = self._profiles[profile_id]
            self._save_profiles()
            return True
        return False
    
    def update_profile(self, profile: PlayerProfile) -> None:
        """Update a profile."""
        self._profiles[profile.id] = profile
        self._save_profiles()
    
    def get_all_profiles(self) -> list:
        """Get all profiles sorted by high score."""
        return sorted(self._profiles.values(), key=lambda p: p.high_score, reverse=True)
    
    @property
    def current_profile(self) -> Optional[PlayerProfile]:
        """Get current active profile."""
        return self._current_profile
    
    @property
    def has_profiles(self) -> bool:
        """Check if any profiles exist."""
        return len(self._profiles) > 0
