"""
Configuration management for the game.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class GameConfig:
    """
    Runtime game configuration.
    All timing and gameplay values that can be adjusted.
    """
    # Display
    window_width: int = 1280
    window_height: int = 720
    fullscreen: bool = False
    vsync: bool = True
    
    # Gameplay timing (frames at 60 FPS)
    das_delay: int = 10
    arr_rate: int = 2
    soft_drop_rate: int = 2
    lock_delay: int = 30
    max_lock_resets: int = 15
    
    # Audio
    master_volume: float = 0.8
    music_volume: float = 0.5
    sfx_volume: float = 0.7
    
    # Controls (key names as strings)
    controls: Dict[str, str] = field(default_factory=lambda: {
        "move_left": "K_LEFT",
        "move_right": "K_RIGHT",
        "soft_drop": "K_DOWN",
        "hard_drop": "K_SPACE",
        "rotate_cw": "K_UP",
        "rotate_ccw": "K_z",
        "rotate_180": "K_a",
        "hold": "K_c",
        "pause": "K_ESCAPE",
        "restart": "K_r",
    })
    
    # Visual
    palette: str = "classic"
    show_ghost: bool = True
    show_grid: bool = True
    particles_enabled: bool = True
    screen_shake_enabled: bool = True
    
    # Gamepad
    gamepad_enabled: bool = True
    gamepad_deadzone: float = 0.3


class Config:
    """
    Configuration manager with save/load support.
    """
    
    DEFAULT_PATH = Path.home() / ".tetris_config.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        self._path = config_path or self.DEFAULT_PATH
        self._config = GameConfig()
        self._dirty = False
    
    @property
    def data(self) -> GameConfig:
        """Get the current configuration."""
        return self._config
    
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self._path.exists():
            return False
        
        try:
            with open(self._path, 'r') as f:
                data = json.load(f)
            
            # Update config with loaded values
            for key, value in data.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
            
            self._dirty = False
            return True
        except (json.JSONDecodeError, IOError):
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self._path, 'w') as f:
                json.dump(asdict(self._config), f, indent=2)
            self._dirty = False
            return True
        except IOError:
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self._config = GameConfig()
        self._dirty = True
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self._dirty = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self._config, key, default)
    
    @property
    def is_dirty(self) -> bool:
        """Check if configuration has unsaved changes."""
        return self._dirty
