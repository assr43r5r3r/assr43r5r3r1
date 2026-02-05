# Signal to Noise - Design Document

## 1. Game Concept

Signal to Noise is a 2D, story-driven systems game where the player is the last human operator routing messages across a fractured network. The game combines puzzle routing, resource management, emergent narrative, and moral choices.

## 2. Core Mechanics

### 2.1 Network Routing

The player must route messages from origin nodes to destination nodes through a network graph. Each link has properties that affect routing decisions:

- **Bandwidth**: Maximum bytes per second
- **Latency**: Base transmission delay
- **Reliability**: Chance of successful transmission
- **Base Risk**: Interception probability baseline

### 2.2 Pathfinding Algorithms

#### Dijkstra's Algorithm
Used for finding the optimal route. Weight function:
```
weight = latency + risk_penalty + congestion_penalty + owner_penalty
```

Where:
- `risk_penalty = base_risk × (1 - reliability) × 2.0`
- `congestion_penalty = (current_load / bandwidth) × 0.5`
- `owner_penalty = 1.0 if hostile faction`

#### Yen's K-Shortest Paths
Provides up to 3 alternative routes for player choice. Players can evaluate trade-offs between speed, safety, and cost.

### 2.3 Bandwidth Simulation

Each link processes a queue of signals:
1. Signals are enqueued when sent
2. Bytes transmitted per tick = bandwidth × dt
3. Signal progress = bytes_transmitted / signal_size
4. When progress reaches 1.0, signal moves to next edge

#### Queue Overflow
When queue exceeds threshold (2× bandwidth):
- Latency increases proportionally
- Packet loss probability rises
- New signals may be dropped

### 2.4 Interception

Interception probability per edge:
```
P = base_risk × (1 - reliability) × attacker_presence × encryption_factor
```

Where:
- `attacker_presence` = 1.0 + (interceptor_count × 0.5)
- `encryption_factor` = 1.0 - (encryption_level × 0.25)

### 2.5 Player Actions

- **Route Message**: Select path and encryption level
- **Bribe Node**: Temporarily increase trust (costs tokens)
- **Encrypt**: Reduce interception risk (costs tokens + adds latency)
- **Forge**: Modify message metadata (discovery risk)

## 3. Resource Economy

### Tokens
Primary currency earned through:
- Successful message delivery (reward amount)
- Faction bonuses
- Milestone achievements

Spent on:
- Encryption (10 tokens per level)
- Bribes (25 tokens per node)
- Network upgrades

### Reputation
Per-faction reputation (-100 to +100):
- Increases: Deliver messages for faction
- Decreases: Intercept faction messages, deliver to enemies
- Effects: Access to faction nodes, special missions

## 4. Faction System

### Factions
1. **Market**: Trade-focused, controls commercial nodes
2. **Militia**: Military faction, hostile to outsiders
3. **Archive**: Information preservationists, neutral
4. **Cult**: Secret faction, unpredictable

### Relations
Factions have relationships with each other:
- Allied factions share intelligence
- Hostile factions place interceptors on shared routes

## 5. AI Systems

### Interceptors
AI-controlled entities that patrol network segments:
- Move between patrol nodes each tick
- Detect signals within range
- Attempt capture based on skill level
- Report to faction on successful intercepts

### Faction AI
Simple strategic behaviors:
- **Expand**: Claim neutral nodes when resources allow
- **Defend**: Strengthen owned nodes
- **Retaliate**: Target player after hostile actions

## 6. Narrative System

### Event Triggers
Events trigger based on conditions:
- Message delivery counts
- Reputation thresholds
- World flags
- Time/day progression

### Dialogue Structure
```json
{
  "speaker": "Character Name",
  "text": "Dialogue content...",
  "choices": [
    {"text": "Option 1", "effects": {"flag": true}},
    {"text": "Option 2", "next_line": 5}
  ]
}
```

### World Flags
Persistent boolean flags that affect:
- Available messages
- Node states
- Faction behaviors
- Story branches

## 7. Story Structure

### Act I: Static
- Tutorial phase
- Learn basic routing
- Minimal interception risk
- Introduces main factions

### Act II: Interference  
- Interceptors become active
- Encryption unlocked
- Faction tensions rise
- Moral choices emerge

### Act III: Broadcast
- Full network available
- Archive mission
- Resource pooling required
- Multiple endings based on flags

## 8. Performance Design

### Fixed Timestep
- Logic: 30 updates per second
- Rendering: Variable (capped at 60 FPS)
- Benefits: Deterministic simulation, stable physics

### Batching
- Links: Single draw call with line batch
- Nodes: Pre-rendered sprites in cache
- Signals: Simple circles, LOD for distant views

### Memory Management
- Reuse surfaces and arrays
- Pool entity IDs
- Lazy font initialization
- Limit concurrent signals (500 max)

### LOD System
When zoomed out or many signals:
- Simplified signal rendering
- Hide node labels
- Aggregate signal icons
- Disable glow effects

## 9. Save System

### Snapshot Contents
```json
{
  "version": "1.0",
  "timestamp": "ISO-8601",
  "metadata": {
    "playtime": 3600,
    "act": 2
  },
  "world_flags": {
    "colony_fallen": true
  },
  "entities": [...],
  "components": {...}
}
```

### Determinism
- Fixed timestep ensures reproducible simulation
- Random seeds stored for events
- Save/load is lossless

## 10. UI Design

### Main Map Screen
- Network visualization (nodes + links)
- Bandwidth bars on links
- Selection highlights
- Mini-map (optional)

### Inbox Panel
- Message list with priority indicators
- Origin/destination display
- Size and reward info
- Click to select for routing

### Inspector Panel
- Node statistics
- Owner and trust info
- Action buttons (Bribe, Logs)

### Routing Panel
- Alternative routes display
- Metrics per route (latency, risk)
- Encryption level slider
- Cost summary

### HUD
- Token count
- Current day/time
- Time scale indicator
- Debug toggle

## 11. Accessibility

### Visual
- High contrast color scheme
- Colorblind-friendly palette options
- Scalable fonts
- Clear UI indicators

### Input
- Full keyboard navigation
- Configurable key bindings
- Mouse and keyboard parity

### Display
- Support for 1024×600 to 1920×1080
- Scalable UI layout
- Optional reduced motion

## 12. Technical Specifications

### Minimum Requirements
- Python 3.10+
- Pygame 2.0+
- Dual-core CPU
- 4 GB RAM
- 100 MB storage

### Target Performance
- 30 FPS minimum on low-end hardware
- 60 FPS on mid-range hardware
- Sub-100ms input latency

### File Formats
- Game data: JSON
- Assets: PNG (sprites), OGG (audio)
- Saves: JSON with version header
