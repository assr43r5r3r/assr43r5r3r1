"""
Global settings and configuration for BlockFall - A Modern Puzzle Game.
All timing values, dimensions, and gameplay constants are defined here.
"""

# Game identity
GAME_NAME = "BlockFall"
GAME_SUBTITLE = "A Modern Puzzle Experience"

# Display settings - Larger window, optimized
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60
WINDOW_TITLE = "BlockFall"

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

# Color palettes - Modern game themes that change the entire look
PALETTES = {
    # Classic dark theme
    "classic": {
        "I": (0, 240, 240),
        "O": (240, 240, 0),
        "T": (160, 0, 240),
        "S": (0, 240, 0),
        "Z": (240, 0, 0),
        "J": (0, 0, 240),
        "L": (240, 160, 0),
        "ghost": (80, 80, 100),
        "background": (15, 15, 25),
        "grid_line": (40, 40, 55),
        "ui_text": (245, 245, 250),
        "ui_accent": (100, 180, 255),
        "ui_secondary": (150, 150, 170),
        "glow": (120, 180, 255),
        "button_bg": (35, 35, 50),
        "button_hover": (55, 55, 75),
        "panel_bg": (25, 25, 40),
    },
    # Neon cyberpunk
    "neon": {
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
    # Ocean blue
    "ocean": {
        "I": (100, 200, 255),
        "O": (200, 230, 180),
        "T": (150, 120, 220),
        "S": (80, 220, 180),
        "Z": (220, 140, 160),
        "J": (80, 130, 200),
        "L": (220, 180, 140),
        "ghost": (60, 80, 100),
        "background": (12, 20, 35),
        "grid_line": (35, 50, 70),
        "ui_text": (230, 245, 255),
        "ui_accent": (80, 180, 255),
        "ui_secondary": (120, 180, 200),
        "glow": (100, 200, 255),
        "button_bg": (25, 40, 60),
        "button_hover": (40, 60, 90),
        "panel_bg": (18, 30, 50),
    },
    # Forest green
    "forest": {
        "I": (100, 220, 180),
        "O": (230, 220, 140),
        "T": (180, 140, 200),
        "S": (100, 200, 120),
        "Z": (220, 130, 130),
        "J": (100, 160, 180),
        "L": (220, 170, 100),
        "ghost": (70, 90, 80),
        "background": (15, 25, 18),
        "grid_line": (40, 55, 45),
        "ui_text": (240, 250, 240),
        "ui_accent": (100, 200, 150),
        "ui_secondary": (160, 200, 160),
        "glow": (120, 220, 160),
        "button_bg": (30, 45, 35),
        "button_hover": (50, 70, 55),
        "panel_bg": (22, 35, 28),
    },
    # Sunset warm
    "sunset": {
        "I": (255, 180, 120),
        "O": (255, 230, 120),
        "T": (200, 140, 180),
        "S": (180, 220, 140),
        "Z": (255, 140, 140),
        "J": (150, 160, 200),
        "L": (255, 200, 100),
        "ghost": (100, 80, 70),
        "background": (30, 20, 18),
        "grid_line": (60, 45, 40),
        "ui_text": (255, 250, 240),
        "ui_accent": (255, 180, 100),
        "ui_secondary": (255, 150, 130),
        "glow": (255, 200, 150),
        "button_bg": (50, 35, 30),
        "button_hover": (75, 55, 45),
        "panel_bg": (40, 28, 25),
    },
    # Midnight purple
    "midnight": {
        "I": (150, 180, 255),
        "O": (255, 220, 180),
        "T": (200, 140, 255),
        "S": (140, 220, 200),
        "Z": (255, 140, 180),
        "J": (120, 140, 220),
        "L": (255, 180, 140),
        "ghost": (80, 70, 100),
        "background": (18, 15, 30),
        "grid_line": (45, 40, 65),
        "ui_text": (245, 240, 255),
        "ui_accent": (180, 140, 255),
        "ui_secondary": (160, 150, 200),
        "glow": (200, 160, 255),
        "button_bg": (40, 35, 55),
        "button_hover": (60, 55, 80),
        "panel_bg": (30, 25, 45),
    },
    # Monochrome grayscale
    "monochrome": {
        "I": (220, 220, 220),
        "O": (180, 180, 180),
        "T": (160, 160, 160),
        "S": (200, 200, 200),
        "Z": (140, 140, 140),
        "J": (120, 120, 120),
        "L": (190, 190, 190),
        "ghost": (80, 80, 80),
        "background": (15, 15, 15),
        "grid_line": (40, 40, 40),
        "ui_text": (245, 245, 245),
        "ui_accent": (200, 200, 200),
        "ui_secondary": (150, 150, 150),
        "glow": (255, 255, 255),
        "button_bg": (35, 35, 35),
        "button_hover": (55, 55, 55),
        "panel_bg": (25, 25, 25),
    },
    # Retro arcade
    "retro": {
        "I": (0, 255, 255),
        "O": (255, 255, 0),
        "T": (255, 0, 255),
        "S": (0, 255, 0),
        "Z": (255, 0, 0),
        "J": (0, 0, 255),
        "L": (255, 128, 0),
        "ghost": (60, 60, 60),
        "background": (0, 0, 0),
        "grid_line": (30, 30, 30),
        "ui_text": (255, 255, 255),
        "ui_accent": (255, 255, 0),
        "ui_secondary": (0, 255, 255),
        "glow": (255, 255, 255),
        "button_bg": (20, 20, 20),
        "button_hover": (40, 40, 40),
        "panel_bg": (10, 10, 10),
    },
    # Cherry blossom
    "cherry": {
        "I": (255, 180, 200),
        "O": (255, 240, 200),
        "T": (220, 160, 200),
        "S": (180, 220, 200),
        "Z": (255, 160, 170),
        "J": (180, 180, 220),
        "L": (255, 200, 180),
        "ghost": (140, 120, 130),
        "background": (35, 25, 30),
        "grid_line": (60, 45, 50),
        "ui_text": (255, 245, 250),
        "ui_accent": (255, 150, 180),
        "ui_secondary": (220, 180, 200),
        "glow": (255, 200, 220),
        "button_bg": (55, 40, 50),
        "button_hover": (80, 60, 70),
        "panel_bg": (45, 32, 40),
    },
    # Ice cold
    "ice": {
        "I": (180, 230, 255),
        "O": (220, 240, 255),
        "T": (180, 200, 240),
        "S": (200, 250, 240),
        "Z": (240, 200, 220),
        "J": (160, 180, 220),
        "L": (230, 220, 200),
        "ghost": (100, 120, 140),
        "background": (15, 22, 30),
        "grid_line": (40, 55, 70),
        "ui_text": (240, 250, 255),
        "ui_accent": (150, 220, 255),
        "ui_secondary": (180, 200, 220),
        "glow": (200, 240, 255),
        "button_bg": (30, 45, 60),
        "button_hover": (45, 65, 85),
        "panel_bg": (22, 35, 48),
    },
}

DEFAULT_PALETTE = "classic"

# List of available themes for cycling
THEME_ORDER = ["classic", "neon", "ocean", "forest", "sunset", "midnight", "monochrome", "retro", "cherry", "ice"]

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
AVATAR_SIZE_GAMEPLAY = 80  # Larger avatar in gameplay
# Generate 10 default avatar slots - user should place images as 1.png, 2.png, etc.
DEFAULT_AVATARS = [f"{i}.png" for i in range(1, 11)]
