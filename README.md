# BlockFall - A Modern Puzzle Experience

A polished Tetris clone built with Python and pygame-ce, featuring modern aesthetics, smooth animations, particles, sound effects, screen shake, and a clean multi-file architecture.

## Features

### Modern Visual Themes
- **10 Beautiful Themes**: Classic, Neon, Ocean, Forest, Sunset, Midnight, Monochrome, Retro, Cherry, Ice
- **Each theme changes the entire game**: Background, UI colors, block colors, glow effects
- **Loading Screen**: Animated loading screen with falling blocks

### Core Gameplay
- **Modern Guideline Tetris Rules**
  - 10×20 playfield with 4 hidden spawn rows
  - 7-bag randomizer with deterministic seed support
  - SRS (Super Rotation System) with correct wall kicks including I-piece
  - Hold piece (one swap per spawn)
  - Ghost piece preview
  - DAS (Delayed Auto Shift) / ARR (Auto Repeat Rate) input handling
  - Soft drop and hard drop
  - Lock delay with reset rules

- **25-Stage System**
  - Progress through 25 unique stages (Beginner to Ultimate)
  - Increasing speed with each stage
  - Score 10 points per row cleared
  - Stage-based progression instead of levels

### Player System
- **Player Profiles**: Create and switch between players
- **10 Avatar Slots**: Select from default avatars or leave empty
- **Leaderboard**: Track high scores (one entry per player, best score only)
- **Auto-save**: Progress saved automatically

### Visual Polish
- 60 FPS target with smooth rendering
- Particle effects for line clears, T-Spins, and hard drops
- Screen shake on big clears
- Line clear animations (flash/fade effects)
- Countdown animation before game start ("3, 2, 1, GO!")
- Falling blocks background on main menu
- Visual keyboard key representations in How To Play panel

### Audio
- Sound effects for all game events
- Separate volume controls for master, music, and SFX
- Procedurally generated placeholder sounds

## Installation

### Requirements
- Python 3.8 or higher
- pygame-ce 2.4.0 or higher

### Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/blockfall.git
cd blockfall

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## Controls

| Action | Keys |
|--------|------|
| Move Left | ← (Left Arrow) or A |
| Move Right | → (Right Arrow) or D |
| Soft Drop | ↓ (Down Arrow) or S |
| Hard Drop | Space |
| Rotate Clockwise | ↑ (Up Arrow) or W |
| Rotate Counter-Clockwise | Z |
| Hold Piece | C |
| Pause | Escape |

## Adding Custom Avatars

To add custom avatar images:

1. Create a folder: `assets/avatars/`
2. Add PNG images (recommended size: 128x128 or larger, square)
3. Name them sequentially: `1.png`, `2.png`, `3.png`, ... up to `10.png`
4. Players can select these when creating profiles

Example folder structure:
```
assets/
└── avatars/
    ├── 1.png   # First avatar option
    ├── 2.png   # Second avatar option
    ├── 3.png   # Third avatar option
    ├── 4.png   # Fourth avatar option
    ├── 5.png   # Fifth avatar option
    ├── 6.png   # Sixth avatar option
    ├── 7.png   # Seventh avatar option
    ├── 8.png   # Eighth avatar option
    ├── 9.png   # Ninth avatar option
    └── 10.png  # Tenth avatar option
```

## Adding Custom Icons (Optional)

You can provide custom icon images for the Options and Leaderboard buttons:

1. Options icon: `assets/icons/options.png` (32x32 recommended)
2. Leaderboard icon: `assets/icons/leaderboard.png` (32x32 recommended)

If icons are not provided, the game will display text symbols as fallback.

## Project Structure

```
blockfall/
├── main.py              # Application entry point
├── settings.py          # Global configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── STORY_MODE.md       # Story mode documentation
├── assets/
│   └── avatars/        # Avatar images (1.png through 10.png)
└── src/
    ├── engine/         # Game loop, timing, configuration
    ├── tetris/         # Core game logic
    ├── input/          # Input handling
    ├── render/         # Rendering
    ├── audio/          # Audio management
    ├── ui/             # User interface
    │   ├── loading.py  # Loading screen
    │   ├── menu.py     # Menus (Main, Pause, Settings)
    │   ├── screens.py  # Name entry, leaderboard
    │   └── overlays.py # Countdown, transitions
    ├── save/           # Save system
    │   ├── profile.py  # Player profiles
    │   └── leaderboard.py
    ├── story/          # Story mode (coming soon)
    └── tests/          # Unit tests
```

## Running Tests

```bash
# Run all tests
python -m pytest src/tests/ -v

# Run specific test file
python -m pytest src/tests/test_srs.py -v
```

## Building Executable

To compile to .exe on Windows:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name BlockFall main.py
```

The executable will be in the `dist/` folder.

## License

MIT License - see LICENSE file for details.

## Credits

Built with [pygame-ce](https://github.com/pygame-community/pygame-ce) - the community edition of pygame.
