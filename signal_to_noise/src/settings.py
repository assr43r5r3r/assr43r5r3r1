"""
Game settings and configuration.

This module contains all game constants and configuration options.
Supports low-end mode for performance optimization.
"""

import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class Settings:
    """Game settings configuration."""
    
    # Display settings
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    FPS_CAP: int = 60
    LOGIC_TICK_RATE: int = 30  # Fixed timestep for game logic (Hz)
    FULLSCREEN: bool = False
    
    # Colors (RGB tuples)
    COLOR_BG: Tuple[int, int, int] = (15, 15, 25)
    COLOR_NODE_TRUSTED: Tuple[int, int, int] = (50, 200, 100)
    COLOR_NODE_NEUTRAL: Tuple[int, int, int] = (200, 180, 50)
    COLOR_NODE_COMPROMISED: Tuple[int, int, int] = (200, 50, 50)
    COLOR_LINK_DEFAULT: Tuple[int, int, int] = (80, 80, 100)
    COLOR_LINK_ACTIVE: Tuple[int, int, int] = (100, 150, 200)
    COLOR_SIGNAL: Tuple[int, int, int] = (100, 200, 255)
    COLOR_UI_BG: Tuple[int, int, int] = (30, 30, 45)
    COLOR_UI_BORDER: Tuple[int, int, int] = (60, 60, 80)
    COLOR_TEXT: Tuple[int, int, int] = (220, 220, 230)
    COLOR_TEXT_HIGHLIGHT: Tuple[int, int, int] = (255, 255, 255)
    
    # Node rendering
    NODE_RADIUS: int = 20
    NODE_GLOW_RADIUS: int = 30
    LINK_WIDTH: int = 3
    SIGNAL_RADIUS: int = 6
    
    # Camera settings
    CAMERA_ZOOM_MIN: float = 0.5
    CAMERA_ZOOM_MAX: float = 2.0
    CAMERA_PAN_SPEED: float = 500.0
    
    # Performance settings (low-end mode)
    LOW_END_MODE: bool = False
    ENABLE_GLOW: bool = True
    ENABLE_PARTICLES: bool = True
    ENABLE_ANTIALIASING: bool = True
    MAX_CONCURRENT_SIGNALS: int = 500
    
    # Gameplay
    STARTING_TOKENS: int = 100
    ENCRYPTION_COST: int = 10
    BRIBE_COST: int = 25
    FORGE_COST: int = 15
    
    # Network simulation
    DEFAULT_BANDWIDTH: int = 2048  # bytes per second
    DEFAULT_LATENCY: float = 0.1  # seconds
    DEFAULT_RELIABILITY: float = 0.9
    DEFAULT_INTERCEPT_RISK: float = 0.1
    QUEUE_THRESHOLD_MULTIPLIER: float = 2.0  # Queue threshold = capacity * multiplier
    PACKET_LOSS_BASE: float = 0.01
    
    # Paths
    ASSETS_PATH: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "assets"
    ))
    DATA_PATH: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data"
    ))
    
    # UI settings
    FONT_SIZE_SMALL: int = 14
    FONT_SIZE_MEDIUM: int = 18
    FONT_SIZE_LARGE: int = 24
    UI_PADDING: int = 10
    UI_MARGIN: int = 5
    INBOX_WIDTH: int = 300
    INSPECTOR_WIDTH: int = 280
    
    # Debug
    DEBUG_OVERLAY: bool = False
    DEBUG_LOG_FILE: str = "game_log.json"

    def enable_low_end_mode(self):
        """Enable low-end mode for better performance on weak hardware."""
        self.LOW_END_MODE = True
        self.ENABLE_GLOW = False
        self.ENABLE_PARTICLES = False
        self.ENABLE_ANTIALIASING = False
        self.MAX_CONCURRENT_SIGNALS = 300
        self.FPS_CAP = 30
        self.NODE_GLOW_RADIUS = 0


# Global settings instance
SETTINGS = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return SETTINGS


def apply_low_end_mode():
    """Apply low-end mode settings globally."""
    SETTINGS.enable_low_end_mode()
