# Signal to Noise

A 2D story-driven systems game where the player is the last human operator routing messages across a fractured network.

## Overview

Signal to Noise combines puzzle routing, resource management, emergent narrative, and moral choices. Set in a post-collapse world, you must guide critical messages through a network of settlements, relays, and hostile territories while managing bandwidth, avoiding interception, and making choices that shape the fate of communities.

## Features

- **Network Routing**: Route messages through a dynamic network with varying bandwidth, latency, and risk levels
- **Resource Management**: Manage tokens to pay for encryption, bribes, and network upgrades
- **Faction System**: Build reputation with different factions through your routing choices
- **Interception Mechanics**: Avoid or outmaneuver AI interceptors patrolling the network
- **Encryption System**: Protect sensitive messages with encryption (at a cost)
- **Three-Act Story**: Progress through Static → Interference → Broadcast

## Requirements

- Python 3.10+
- Pygame (or Pygame-CE)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd signal_to_noise

# Install dependencies
pip install pygame pytest

# Run the game
python -m src.main
```

## Command Line Options

```bash
python -m src.main [options]

Options:
  --low-end       Enable low-end mode for better performance
  --fullscreen    Run in fullscreen mode
  --width WIDTH   Set window width (default: 1280)
  --height HEIGHT Set window height (default: 720)
  --debug         Enable debug overlay
```

## Controls

### Keyboard
- **Arrow Keys / WASD**: Pan camera
- **+/-**: Zoom in/out
- **Space**: Pause/unpause
- **1/2/3**: Set time scale (1x, 2x, 4x)
- **Escape**: Open pause menu
- **F3**: Toggle debug overlay

### Mouse
- **Left Click**: Select node
- **Double Click**: Inspect node
- **Right Click + Drag**: Pan camera
- **Scroll Wheel**: Zoom

## Project Structure

```
signal_to_noise/
├── assets/                # Art and audio assets
│   ├── sprites/
│   ├── ui/
│   └── audio/
├── data/
│   ├── nodes.json         # Network node definitions
│   ├── links.json         # Network link definitions
│   ├── messages/          # Message templates
│   └── scenarios/         # Story scenario files
├── src/
│   ├── main.py            # Entry point
│   ├── settings.py        # Game configuration
│   ├── app.py             # Game shell & state manager
│   ├── data_loader.py     # JSON data loading
│   ├── states/            # Game states
│   │   ├── base_state.py
│   │   ├── menu_state.py
│   │   ├── game_state.py
│   │   ├── routing_state.py
│   │   └── event_state.py
│   ├── ecs/               # Entity Component System
│   │   ├── ecs_core.py    # Core ECS implementation
│   │   ├── components.py  # All components
│   │   └── systems/       # Game systems
│   ├── ui/                # UI widgets
│   │   ├── ui_manager.py
│   │   └── widgets.py
│   └── utils/             # Utilities
│       ├── routing.py     # Pathfinding algorithms
│       ├── save.py        # Save/load system
│       └── debug.py       # Debug overlay
└── tests/                 # Unit and integration tests
```

## Core Systems

### Routing System
Uses weighted Dijkstra's algorithm for optimal path finding. Supports Yen's k-shortest paths algorithm to provide players with multiple route options.

Weight function considers:
- Link latency
- Interception risk (base_risk × (1 - reliability))
- Bandwidth congestion
- Owner penalties for hostile factions

### Bandwidth System
Simulates realistic network queuing:
- Per-link capacity in bytes/second
- Queue-based transmission
- Congestion increases latency
- Overload causes packet loss

### Interception System
Probability-based interception:
```
P_intercept = base_risk × (1 - reliability) × attacker_factor × encryption_factor
```

Encryption reduces interception probability by a multiplicative factor.

## Running Tests

```bash
# Install pytest
pip install pytest

# Run all tests
cd signal_to_noise
pytest tests/ -v

# Run specific test files
pytest tests/test_routing.py -v
pytest tests/test_bandwidth.py -v
pytest tests/test_serialization.py -v
```

## Performance

The game is designed for low-end hardware:

**Target Specs:**
- Dual-core CPU (Intel Core i3 or equivalent)
- 4 GB RAM
- Integrated GPU (Intel HD)
- Windows 10/11 or Linux

**Optimizations:**
- Fixed timestep game loop (30Hz logic, variable FPS rendering)
- Batched rendering for links and signals
- Pre-rendered node sprites with caching
- Signal count limits with queue management
- LOD system for zoomed-out views
- Optional low-end mode (--low-end flag)

## Data Formats

### nodes.json
```json
[
  {
    "id": "A",
    "name": "Harbor Station",
    "x": 150,
    "y": 200,
    "capacity": 10240,
    "trust": 0.8,
    "owner": null,
    "type": "settlement"
  }
]
```

### links.json
```json
[
  {
    "a": "A",
    "b": "B",
    "bandwidth": 2048,
    "latency": 0.1,
    "reliability": 0.95,
    "base_risk": 0.05
  }
]
```

### Message Format
```json
{
  "id": "M001",
  "origin": "Harbor",
  "dest": "Medical-Hub",
  "tag": "med",
  "priority": 9,
  "size": 4096,
  "reward": 60,
  "content_snippet": "reports of a fast-acting fever",
  "meta": {"time_limit": 180}
}
```

## Save System

Games are saved as JSON files containing:
- All entity data (nodes, links, signals)
- Component states
- World flags (narrative triggers)
- Player resources and reputation

Save files are deterministic and portable.

## License

See LICENSE file for details.

## Development Notes

### Architecture Decisions

1. **ECS Pattern**: Used for flexibility and performance. Components are pure data; systems contain all logic.

2. **Fixed Timestep**: Game logic runs at 30Hz for deterministic simulation. Rendering is variable FPS.

3. **State Machine**: Game states (menu, game, routing, event) are separate classes for clean organization.

4. **Data-Driven**: Network topology, messages, and scenarios are loaded from JSON files.

### Key Algorithms

- **Dijkstra**: O(E log V) shortest path with custom weight function
- **Yen's K-Shortest**: O(K × V × E log V) for alternative routes
- **Bandwidth Queue**: O(1) per-signal processing with throughput limits

### Future Improvements

- [ ] Audio system implementation
- [ ] Particle effects for signals
- [ ] More sophisticated AI behaviors
- [ ] Mod support for custom scenarios
- [ ] Localization system
