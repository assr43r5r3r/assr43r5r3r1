"""
ECS Components for Signal to Noise.

All game components are defined here as dataclasses for clarity and immutability.
Components are pure data containers with no behavior.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum, auto


class FactionType(Enum):
    """Types of factions in the game."""
    NEUTRAL = auto()
    PLAYER = auto()
    MARKET = auto()
    MILITIA = auto()
    CULT = auto()
    ARCHIVE = auto()


class MessageTag(Enum):
    """Message content tags for categorization."""
    TRADE = "trade"
    MED = "med"
    MILITARY = "military"
    PERSONAL = "personal"
    INTEL = "intel"
    EMERGENCY = "emergency"


@dataclass
class Position:
    """
    2D position component.
    
    Attributes:
        x: X coordinate in world space
        y: Y coordinate in world space
    """
    x: float = 0.0
    y: float = 0.0
    
    def as_tuple(self) -> Tuple[float, float]:
        """Return position as tuple."""
        return (self.x, self.y)
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position."""
        import math
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class Renderable:
    """
    Rendering information for an entity.
    
    Attributes:
        sprite_name: Name of sprite asset to use (or None for shapes)
        color: RGB color tuple for rendering
        radius: Radius for circular entities
        layer: Rendering layer (higher = drawn later/on top)
        visible: Whether the entity should be rendered
        alpha: Transparency (0-255)
    """
    sprite_name: Optional[str] = None
    color: Tuple[int, int, int] = (255, 255, 255)
    radius: int = 10
    layer: int = 0
    visible: bool = True
    alpha: int = 255


@dataclass
class NetworkNode:
    """
    A node in the network graph (settlement, relay, etc.)
    
    Attributes:
        node_id: Unique string identifier for the node
        owner: Faction that controls this node (or None for neutral)
        capacity: Maximum queue size in bytes
        trust: Trust level (0.0 - 1.0), affects message reliability
        buffer: Current messages/signals queued at this node
        stats: Statistical tracking for analytics
        name: Display name for the node
        node_type: Type of node (relay, settlement, hub, etc.)
    """
    node_id: str = ""
    owner: Optional[str] = None
    capacity: int = 10240
    trust: float = 0.7
    buffer: List[int] = field(default_factory=list)  # List of entity IDs queued
    stats: Dict[str, Any] = field(default_factory=dict)
    name: str = ""
    node_type: str = "relay"
    
    def __post_init__(self):
        if not self.name:
            self.name = self.node_id
        if 'messages_sent' not in self.stats:
            self.stats = {
                'messages_sent': 0,
                'messages_received': 0,
                'messages_intercepted': 0,
                'total_bytes': 0
            }


@dataclass
class NetworkLink:
    """
    A connection between two network nodes.
    
    Attributes:
        a: ID of first node
        b: ID of second node
        bandwidth: Maximum bytes per second that can traverse this link
        latency: Base latency in seconds
        reliability: Reliability factor (0.0 - 1.0)
        base_risk: Base interception risk (0.0 - 1.0)
        current_load: Current bytes queued for transmission
        queue: List of signal entity IDs waiting to traverse
        active: Whether the link is operational
    """
    a: str = ""
    b: str = ""
    bandwidth: int = 2048
    latency: float = 0.1
    reliability: float = 0.9
    base_risk: float = 0.1
    current_load: int = 0
    queue: List[int] = field(default_factory=list)
    active: bool = True
    
    def get_other_node(self, node_id: str) -> str:
        """Get the other node in this link."""
        return self.b if node_id == self.a else self.a
    
    def get_effective_latency(self) -> float:
        """Calculate effective latency based on current load."""
        load_factor = self.current_load / max(self.bandwidth, 1)
        return self.latency * (1 + load_factor * 0.5)


@dataclass
class Message:
    """
    A message waiting to be routed.
    
    Attributes:
        msg_id: Unique message identifier
        origin: Node ID where message originated
        dest: Destination node ID
        tag: Content category tag
        priority: Priority level (1-10, higher = more urgent)
        size: Size in bytes
        reward: Token reward for successful delivery
        content_snippet: Brief content preview for UI
        meta: Additional metadata (time_limit, etc.)
        encrypted: Whether the message is encrypted
        forged: Whether the message metadata has been forged
    """
    msg_id: str = ""
    origin: str = ""
    dest: str = ""
    tag: str = "personal"
    priority: int = 5
    size: int = 1024
    reward: int = 10
    content_snippet: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)
    encrypted: bool = False
    forged: bool = False
    encryption_level: int = 0  # 0-3, higher = stronger


@dataclass
class Signal:
    """
    A message actively being transmitted through the network.
    
    Attributes:
        path: List of node IDs representing the route
        message_ref: Entity ID of the associated Message entity
        current_index: Current position in the path (edge index)
        progress: Progress along current edge (0.0 - 1.0)
        ttl: Time to live in seconds
        encrypted: Whether the signal is encrypted
        size: Size in bytes
        bytes_transmitted: Bytes already sent on current edge
        state: Current state (traveling, queued, delivered, intercepted)
    """
    path: List[str] = field(default_factory=list)
    message_ref: int = 0
    current_index: int = 0
    progress: float = 0.0
    ttl: float = 300.0  # 5 minutes default
    encrypted: bool = False
    size: int = 1024
    bytes_transmitted: int = 0
    state: str = "traveling"  # traveling, queued, delivered, intercepted, dropped


@dataclass
class Faction:
    """
    A faction in the game world.
    
    Attributes:
        faction_id: Unique identifier
        reputation: Player reputation with this faction (-100 to 100)
        resources: Faction's available resources
        relations: Relations with other factions {faction_id: value}
        name: Display name
        color: Faction color for UI
    """
    faction_id: str = ""
    reputation: int = 0
    resources: int = 100
    relations: Dict[str, int] = field(default_factory=dict)
    name: str = ""
    color: Tuple[int, int, int] = (128, 128, 128)
    
    def __post_init__(self):
        if not self.name:
            self.name = self.faction_id


@dataclass
class Timer:
    """
    Generic timer/cooldown component.
    
    Attributes:
        duration: Total duration in seconds
        elapsed: Time elapsed since timer started
        loop: Whether timer should reset when complete
        callback_event: Event to emit when timer completes
        active: Whether timer is currently running
    """
    duration: float = 1.0
    elapsed: float = 0.0
    loop: bool = False
    callback_event: str = ""
    active: bool = True
    
    def tick(self, dt: float) -> bool:
        """
        Update timer and return True if completed.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if timer completed this tick
        """
        if not self.active:
            return False
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            if self.loop:
                self.elapsed = self.elapsed % self.duration
            else:
                self.active = False
            return True
        return False
    
    def reset(self) -> None:
        """Reset the timer."""
        self.elapsed = 0.0
        self.active = True
    
    @property
    def remaining(self) -> float:
        """Get remaining time."""
        return max(0.0, self.duration - self.elapsed)
    
    @property
    def progress(self) -> float:
        """Get progress as 0.0 to 1.0."""
        return min(1.0, self.elapsed / max(0.001, self.duration))


@dataclass
class Interceptor:
    """
    An AI interceptor that can capture signals.
    
    Attributes:
        interceptor_id: Unique identifier
        owner: Faction that controls this interceptor
        patrol_nodes: List of node IDs this interceptor patrols
        current_node: Current node position
        detection_range: Range in graph hops to detect signals
        capture_skill: Skill level for capturing (0.0 - 1.0)
        active: Whether interceptor is currently active
    """
    interceptor_id: str = ""
    owner: str = ""
    patrol_nodes: List[str] = field(default_factory=list)
    current_node: str = ""
    detection_range: int = 1
    capture_skill: float = 0.5
    active: bool = True


@dataclass
class EventTrigger:
    """
    Trigger for narrative events.
    
    Attributes:
        event_id: Unique event identifier
        conditions: Conditions that must be met to trigger
        triggered: Whether this event has already fired
        repeatable: Whether event can trigger multiple times
        priority: Priority for event resolution
    """
    event_id: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    triggered: bool = False
    repeatable: bool = False
    priority: int = 0


@dataclass
class Camera:
    """
    Camera component for viewport control.
    
    Attributes:
        x: Camera center X position
        y: Camera center Y position
        zoom: Current zoom level
        target_x: Target X for smooth panning
        target_y: Target Y for smooth panning
        target_zoom: Target zoom for smooth zooming
    """
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0
    target_x: float = 0.0
    target_y: float = 0.0
    target_zoom: float = 1.0
    
    def world_to_screen(self, wx: float, wy: float, screen_w: int, screen_h: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        sx = int((wx - self.x) * self.zoom + screen_w / 2)
        sy = int((wy - self.y) * self.zoom + screen_h / 2)
        return (sx, sy)
    
    def screen_to_world(self, sx: int, sy: int, screen_w: int, screen_h: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        wx = (sx - screen_w / 2) / self.zoom + self.x
        wy = (sy - screen_h / 2) / self.zoom + self.y
        return (wx, wy)
