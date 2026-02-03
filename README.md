# Modern Tetris

A polished, modern Tetris clone built with Python and pygame-ce, featuring smooth animations, particles, sound effects, screen shake, and a clean multi-file architecture.

## Features

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

- **Scoring System**
  - Line clears (single, double, triple, Tetris)
  - T-Spin detection (mini and full)
  - Back-to-back bonuses
  - Combos
  - Perfect clear detection
  - Level progression with increasing gravity

### Visual Polish
- 60 FPS target with smooth rendering
- Particle effects for line clears, T-Spins, and hard drops
- Screen shake on big clears
- Multiple color palettes (Classic, Neon, Pastel)
- Modern flat UI with glow effects

### Audio
- Sound effects for all game events
- Separate volume controls for master, music, and SFX
- Procedurally generated placeholder sounds

### Technical Features
- Fixed timestep game loop for deterministic gameplay
- Event-driven architecture (game logic decoupled from rendering/audio)
- Particle pooling (no per-frame allocations)
- Input buffering for responsive controls
- Deterministic replay system

## Installation

### Requirements
- Python 3.8 or higher
- pygame-ce 2.4.0 or higher

### Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/modern-tetris.git
cd modern-tetris

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## Controls

| Action | Key |
|--------|-----|
| Move Left | ← (Left Arrow) |
| Move Right | → (Right Arrow) |
| Soft Drop | ↓ (Down Arrow) |
| Hard Drop | Space |
| Rotate Clockwise | ↑ (Up Arrow) |
| Rotate Counter-Clockwise | Z |
| Rotate 180° | A |
| Hold Piece | C |
| Pause | Escape |
| Restart | R |

## Project Structure

```
tetris_project/
├── main.py              # Application entry point
├── settings.py          # Global configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── src/
    ├── engine/         # Game loop, timing, configuration
    │   ├── game_loop.py
    │   ├── timer.py
    │   └── config.py
    ├── tetris/         # Core game logic
    │   ├── game.py     # Main game controller
    │   ├── board.py    # Playfield logic
    │   ├── pieces.py   # Piece definitions
    │   ├── srs.py      # Super Rotation System
    │   ├── bag.py      # 7-bag randomizer
    │   ├── scoring.py  # Scoring system
    │   └── replay.py   # Replay recording/playback
    ├── input/          # Input handling
    │   ├── input_handler.py
    │   └── input_buffer.py
    ├── render/         # Rendering
    │   ├── renderer.py
    │   └── particles.py
    ├── audio/          # Audio management
    │   └── audio_manager.py
    ├── ui/             # User interface
    │   ├── hud.py
    │   └── menu.py
    ├── util/           # Utilities
    │   ├── math_utils.py
    │   ├── pool.py
    │   └── events.py
    └── tests/          # Unit tests
        ├── test_srs.py
        ├── test_bag.py
        ├── test_lock_delay.py
        └── test_replay.py
```

## Running Tests

```bash
# Run all tests
python -m pytest src/tests/ -v

# Run specific test file
python -m pytest src/tests/test_srs.py -v

# Run with unittest
python -m unittest discover -s src/tests -v
```

## Configuration

Game settings can be modified in `settings.py`:

- **Display**: Window size, FPS target
- **Input Timing**: DAS delay, ARR rate, soft drop rate
- **Gameplay**: Lock delay, gravity levels per level
- **Audio**: Volume levels
- **Visuals**: Color palettes, particle settings

## Architecture

### Game Logic Separation
The game logic in `src/tetris/` is completely independent of rendering and audio. This allows for:
- Deterministic replays
- Headless testing
- Future network multiplayer

### Event System
An event bus (`src/util/events.py`) decouples game events from their handlers:
- Game emits events (line clear, T-Spin, etc.)
- Renderer and audio subscribe to relevant events
- No direct dependencies between systems

### Fixed Timestep
The game loop uses fixed timestep updates:
- Logic updates at exactly 60 FPS
- Rendering can run at any speed
- Ensures deterministic gameplay regardless of frame rate

## Scoring Reference

| Action | Points |
|--------|--------|
| Single | 100 × level |
| Double | 300 × level |
| Triple | 500 × level |
| Tetris | 800 × level |
| T-Spin | 400 × level |
| T-Spin Single | 800 × level |
| T-Spin Double | 1200 × level |
| T-Spin Triple | 1600 × level |
| Mini T-Spin | 100 × level |
| Perfect Clear | 3000 × level |
| Combo | 50 × combo × level |
| Back-to-Back | 1.5× multiplier |
| Soft Drop | 1 per cell |
| Hard Drop | 2 per cell |

## License

MIT License - see LICENSE file for details.

## Credits

Built with [pygame-ce](https://github.com/pygame-community/pygame-ce) - the community edition of pygame.
