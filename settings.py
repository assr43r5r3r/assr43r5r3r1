"""
Global settings and configuration for Blokkun - A Manga-Style Puzzle Game.
All timing values, dimensions, and gameplay constants are defined here.
"""

# Game identity
GAME_NAME = "Blokkun"
GAME_SUBTITLE = "A Manga Puzzle Adventure"

# Display settings - Larger window, optimized
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60
WINDOW_TITLE = "Blokkun"

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

# Scoring - simplified: 10 points per row
SCORE_PER_ROW = 10

# Stage system (replaces levels)
MAX_STAGES = 25
NEXT_PIECES_PREVIEW = 3  # Show only 3 next pieces

# Visual settings
PARTICLE_POOL_SIZE = 500
SCREEN_SHAKE_DECAY = 0.85
SCREEN_SHAKE_MAX = 15

# Color palettes - Manga/Anime themed
PALETTES = {
    # Classic manga black and white
    "manga_bw": {
        "I": (220, 220, 220),
        "O": (180, 180, 180),
        "T": (160, 160, 160),
        "S": (200, 200, 200),
        "Z": (140, 140, 140),
        "J": (120, 120, 120),
        "L": (190, 190, 190),
        "ghost": (80, 80, 80),
        "background": (15, 15, 20),
        "grid_line": (50, 50, 55),
        "ui_text": (245, 245, 250),
        "ui_accent": (200, 200, 210),
        "ui_secondary": (150, 150, 160),
        "glow": (255, 255, 255),
        "button_bg": (35, 35, 45),
        "button_hover": (55, 55, 70),
        "panel_bg": (25, 25, 35),
    },
    # Vibrant anime colors
    "anime": {
        "I": (100, 220, 255),
        "O": (255, 230, 100),
        "T": (220, 130, 255),
        "S": (130, 255, 160),
        "Z": (255, 120, 140),
        "J": (130, 160, 255),
        "L": (255, 180, 120),
        "ghost": (100, 100, 120),
        "background": (18, 18, 28),
        "grid_line": (45, 45, 65),
        "ui_text": (255, 255, 255),
        "ui_accent": (255, 150, 200),
        "ui_secondary": (150, 200, 255),
        "glow": (255, 200, 230),
        "button_bg": (45, 35, 60),
        "button_hover": (70, 55, 90),
        "panel_bg": (30, 25, 45),
    },
    # Kawaii pastel
    "kawaii": {
        "I": (180, 230, 255),
        "O": (255, 250, 180),
        "T": (230, 190, 255),
        "S": (190, 255, 210),
        "Z": (255, 190, 200),
        "J": (190, 200, 255),
        "L": (255, 210, 180),
        "ghost": (160, 160, 180),
        "background": (45, 40, 55),
        "grid_line": (70, 65, 85),
        "ui_text": (255, 245, 250),
        "ui_accent": (255, 180, 210),
        "ui_secondary": (180, 220, 255),
        "glow": (255, 220, 240),
        "button_bg": (60, 50, 75),
        "button_hover": (85, 70, 100),
        "panel_bg": (50, 45, 65),
    },
    # Dark anime neon
    "neon_anime": {
        "I": (0, 255, 255),
        "O": (255, 255, 0),
        "T": (255, 0, 255),
        "S": (0, 255, 128),
        "Z": (255, 64, 128),
        "J": (64, 128, 255),
        "L": (255, 160, 0),
        "ghost": (60, 60, 80),
        "background": (8, 8, 16),
        "grid_line": (30, 30, 50),
        "ui_text": (255, 255, 255),
        "ui_accent": (0, 255, 200),
        "ui_secondary": (255, 100, 200),
        "glow": (150, 255, 255),
        "button_bg": (20, 25, 40),
        "button_hover": (35, 45, 70),
        "panel_bg": (15, 18, 30),
    },
    # Shonen action
    "shonen": {
        "I": (80, 200, 255),
        "O": (255, 220, 80),
        "T": (180, 100, 255),
        "S": (100, 255, 130),
        "Z": (255, 80, 100),
        "J": (80, 120, 255),
        "L": (255, 150, 80),
        "ghost": (90, 90, 110),
        "background": (20, 15, 25),
        "grid_line": (50, 40, 60),
        "ui_text": (255, 255, 255),
        "ui_accent": (255, 200, 80),
        "ui_secondary": (255, 120, 80),
        "glow": (255, 180, 100),
        "button_bg": (50, 35, 45),
        "button_hover": (80, 55, 70),
        "panel_bg": (35, 25, 35),
    },
    # Shojo romance
    "shojo": {
        "I": (200, 220, 255),
        "O": (255, 240, 200),
        "T": (255, 180, 220),
        "S": (200, 255, 220),
        "Z": (255, 180, 190),
        "J": (180, 200, 255),
        "L": (255, 200, 180),
        "ghost": (150, 140, 160),
        "background": (40, 30, 45),
        "grid_line": (70, 55, 80),
        "ui_text": (255, 250, 255),
        "ui_accent": (255, 150, 200),
        "ui_secondary": (200, 180, 255),
        "glow": (255, 200, 230),
        "button_bg": (60, 45, 70),
        "button_hover": (90, 65, 100),
        "panel_bg": (50, 38, 58),
    },
    # Retro anime (80s/90s style)
    "retro_anime": {
        "I": (100, 200, 220),
        "O": (240, 220, 120),
        "T": (180, 120, 200),
        "S": (120, 200, 140),
        "Z": (220, 120, 130),
        "J": (100, 140, 200),
        "L": (220, 160, 100),
        "ghost": (100, 100, 110),
        "background": (25, 25, 35),
        "grid_line": (55, 50, 65),
        "ui_text": (250, 245, 240),
        "ui_accent": (220, 180, 140),
        "ui_secondary": (180, 200, 220),
        "glow": (240, 220, 200),
        "button_bg": (45, 40, 55),
        "button_hover": (70, 60, 80),
        "panel_bg": (35, 32, 45),
    },
    # Mecha/Sci-fi anime
    "mecha": {
        "I": (80, 180, 220),
        "O": (220, 200, 80),
        "T": (160, 100, 200),
        "S": (80, 200, 120),
        "Z": (200, 80, 100),
        "J": (80, 120, 200),
        "L": (200, 140, 80),
        "ghost": (70, 80, 100),
        "background": (12, 16, 24),
        "grid_line": (35, 45, 60),
        "ui_text": (220, 230, 255),
        "ui_accent": (100, 200, 255),
        "ui_secondary": (200, 150, 100),
        "glow": (150, 200, 255),
        "button_bg": (25, 35, 50),
        "button_hover": (40, 55, 80),
        "panel_bg": (18, 25, 38),
    },
}

DEFAULT_PALETTE = "anime"

# List of available themes for cycling
THEME_ORDER = ["anime", "kawaii", "manga_bw", "neon_anime", "shonen", "shojo", "retro_anime", "mecha"]

# Audio settings
MASTER_VOLUME = 0.8
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.7

# Key bindings (pygame key codes) - WASD and Arrow keys, no 180 rotation
DEFAULT_CONTROLS = {
    "move_left": ["K_LEFT", "K_a"],
    "move_right": ["K_RIGHT", "K_d"],
    "soft_drop": ["K_DOWN", "K_s"],
    "hard_drop": "K_SPACE",
    "rotate_cw": ["K_UP", "K_w"],
    "rotate_ccw": "K_z",
    "hold": "K_c",
    "pause": "K_ESCAPE",
}

# Gamepad settings
GAMEPAD_ENABLED = True
GAMEPAD_DEADZONE = 0.3

# Save directory
SAVE_DIRECTORY = "saves"

# Avatar settings
AVATAR_DIRECTORY = "assets/avatars"
AVATAR_SIZE_MENU = 48
AVATAR_SIZE_GAMEPLAY = 60
DEFAULT_AVATARS = [
    "avatar_1.png",  # Cute anime character
    "avatar_2.png",  # Cool protagonist
    "avatar_3.png",  # Chibi character
    "avatar_4.png",  # Mysterious character
]
