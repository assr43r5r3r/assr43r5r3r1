# Blokkun - A Manga Puzzle Adventure

A polished, manga-style Tetris clone built with Python and pygame-ce, featuring anime aesthetics, smooth animations, particles, sound effects, screen shake, and a clean multi-file architecture.

## Features

### Manga/Anime Theme
- **8 Beautiful Themes**: Anime, Kawaii, Manga B&W, Neon Anime, Shonen, Shojo, Retro Anime, Mecha
- **Manga-style UI**: Speech bubble tooltips, stylized menus, anime-inspired visuals
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
- **Avatar Support**: Upload custom avatars or use defaults
- **Leaderboard**: Track high scores (one entry per player, best score only)
- **Auto-save**: Progress saved automatically

### Visual Polish
- 60 FPS target with smooth rendering
- Particle effects for line clears, T-Spins, and hard drops
- Screen shake on big clears
- Line clear animations (flash/fade effects)
- Countdown animation before game start ("3, 2, 1, GO!")

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
git clone https://github.com/your-repo/blokkun.git
cd blokkun

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
3. Name them: `avatar_1.png`, `avatar_2.png`, `avatar_3.png`, `avatar_4.png`
4. Players can select these when creating profiles, or upload their own

Example folder structure:
```
assets/
└── avatars/
    ├── avatar_1.png  # Cute anime character
    ├── avatar_2.png  # Cool protagonist
    ├── avatar_3.png  # Chibi character
    └── avatar_4.png  # Mysterious character
```

## Project Structure

```
blokkun/
├── main.py              # Application entry point
├── settings.py          # Global configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── STORY_MODE.md       # Story mode documentation
├── assets/
│   └── avatars/        # Avatar images
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
pyinstaller --onefile --windowed --name Blokkun main.py
```

The executable will be in the `dist/` folder.

## License

MIT License - see LICENSE file for details.

## Credits

Built with [pygame-ce](https://github.com/pygame-community/pygame-ce) - the community edition of pygame.
