"""
Global settings and configuration for the Tetris game.
All timing values, dimensions, and gameplay constants are defined here.
"""

# Display settings
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "Modern Tetris"

# Grid settings
GRID_WIDTH = 10
GRID_HEIGHT = 20
HIDDEN_ROWS = 4  # Rows above visible area for spawning
TOTAL_HEIGHT = GRID_HEIGHT + HIDDEN_ROWS
CELL_SIZE = 30

# Input timing (in frames at 60 FPS)
DAS_DELAY = 10  # Delayed Auto Shift delay (~167ms)
ARR_RATE = 2    # Auto Repeat Rate (~33ms)
SOFT_DROP_RATE = 2  # Soft drop speed multiplier

# Lock delay settings
LOCK_DELAY_FRAMES = 30  # 500ms at 60 FPS
MAX_LOCK_RESETS = 15    # Maximum number of lock delay resets

# Gravity settings (frames per cell drop)
GRAVITY_LEVELS = {
    0: 48,   # Level 0: 0.8 seconds per cell
    1: 43,
    2: 38,
    3: 33,
    4: 28,
    5: 23,
    6: 18,
    7: 13,
    8: 8,
    9: 6,
    10: 5,
    11: 5,
    12: 5,
    13: 4,
    14: 4,
    15: 4,
    16: 3,
    17: 3,
    18: 3,
    19: 2,
    20: 2,  # 20G starts here in some modes
}

# Scoring
SCORE_SINGLE = 100
SCORE_DOUBLE = 300
SCORE_TRIPLE = 500
SCORE_TETRIS = 800
SCORE_TSPIN_MINI = 100
SCORE_TSPIN = 400
SCORE_TSPIN_SINGLE = 800
SCORE_TSPIN_DOUBLE = 1200
SCORE_TSPIN_TRIPLE = 1600
SCORE_PERFECT_CLEAR = 3000
SCORE_COMBO_MULTIPLIER = 50
SCORE_B2B_MULTIPLIER = 1.5

# Lines per level
LINES_PER_LEVEL = 10

# Visual settings
PARTICLE_POOL_SIZE = 500
SCREEN_SHAKE_DECAY = 0.85
SCREEN_SHAKE_MAX = 15

# Color palettes
PALETTES = {
    "classic": {
        "I": (0, 240, 240),
        "O": (240, 240, 0),
        "T": (160, 0, 240),
        "S": (0, 240, 0),
        "Z": (240, 0, 0),
        "J": (0, 0, 240),
        "L": (240, 160, 0),
        "ghost": (128, 128, 128),
        "background": (20, 20, 30),
        "grid_line": (40, 40, 60),
        "ui_text": (255, 255, 255),
        "ui_accent": (100, 200, 255),
        "glow": (255, 255, 255),
    },
    "neon": {
        "I": (0, 255, 255),
        "O": (255, 255, 100),
        "T": (200, 100, 255),
        "S": (100, 255, 100),
        "Z": (255, 100, 100),
        "J": (100, 150, 255),
        "L": (255, 180, 100),
        "ghost": (80, 80, 100),
        "background": (10, 10, 20),
        "grid_line": (30, 30, 50),
        "ui_text": (220, 220, 255),
        "ui_accent": (150, 255, 200),
        "glow": (200, 200, 255),
    },
    "pastel": {
        "I": (150, 220, 220),
        "O": (240, 230, 150),
        "T": (200, 150, 220),
        "S": (150, 220, 150),
        "Z": (220, 150, 150),
        "J": (150, 170, 220),
        "L": (230, 190, 150),
        "ghost": (180, 180, 190),
        "background": (40, 40, 50),
        "grid_line": (60, 60, 75),
        "ui_text": (240, 240, 250),
        "ui_accent": (180, 220, 200),
        "glow": (240, 240, 255),
    },
}

DEFAULT_PALETTE = "classic"

# Audio settings
MASTER_VOLUME = 0.8
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.7

# Key bindings (pygame key codes)
DEFAULT_CONTROLS = {
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
}

# Gamepad settings
GAMEPAD_ENABLED = True
GAMEPAD_DEADZONE = 0.3
