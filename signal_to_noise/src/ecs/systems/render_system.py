"""
Render System for layered rendering with camera support.

Handles batched drawing of nodes, links, signals, and UI elements.
Optimized for low-end hardware with optional glow effects and LOD.
"""

import pygame
from typing import Dict, Tuple, Optional, List, Any
from ..ecs_core import System, World
from ..components import Position, Renderable, NetworkNode, NetworkLink, Signal, Camera
from ...settings import get_settings


class RenderSystem(System):
    """
    System for rendering all visual elements.
    
    Features:
    - Layered rendering (background -> links -> nodes -> signals -> UI)
    - Camera/zoom support
    - Batched line drawing for links
    - Optional glow effects (disabled in low-end mode)
    - Selection highlighting
    """
    
    def __init__(self, screen: pygame.Surface):
        super().__init__()
        self.screen = screen
        self.settings = get_settings()
        
        # Pre-rendered surfaces cache
        self._node_cache: Dict[str, pygame.Surface] = {}
        self._glow_cache: Dict[str, pygame.Surface] = {}
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        
        # Selection state
        self.selected_node_id: Optional[str] = None
        self.hovered_node_id: Optional[str] = None
        
        # Camera reference (set externally)
        self.camera: Optional[Camera] = None
        
        # LOD settings
        self.lod_signal_threshold = 100  # Simplify signals above this count
        self.lod_zoom_threshold = 0.7   # Simplify below this zoom
        
    def initialize(self) -> None:
        """Initialize fonts and cached surfaces."""
        pygame.font.init()
        self._font = pygame.font.Font(None, self.settings.FONT_SIZE_MEDIUM)
        self._small_font = pygame.font.Font(None, self.settings.FONT_SIZE_SMALL)
        self._create_node_surfaces()
    
    def _create_node_surfaces(self) -> None:
        """Pre-render node sprites for different states."""
        radius = self.settings.NODE_RADIUS
        colors = {
            'trusted': self.settings.COLOR_NODE_TRUSTED,
            'neutral': self.settings.COLOR_NODE_NEUTRAL,
            'compromised': self.settings.COLOR_NODE_COMPROMISED
        }
        
        for name, color in colors.items():
            # Main node surface
            size = radius * 2 + 4
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surface, color, (size // 2, size // 2), radius)
            pygame.draw.circle(surface, (255, 255, 255), (size // 2, size // 2), radius, 2)
            self._node_cache[name] = surface
            
            # Glow surface (if enabled)
            if self.settings.ENABLE_GLOW:
                glow_size = self.settings.NODE_GLOW_RADIUS * 2 + 4
                glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                for r in range(self.settings.NODE_GLOW_RADIUS, radius, -2):
                    alpha = int(60 * (1 - (r - radius) / (self.settings.NODE_GLOW_RADIUS - radius)))
                    glow_color = (*color, alpha)
                    pygame.draw.circle(glow_surface, glow_color, 
                                      (glow_size // 2, glow_size // 2), r)
                self._glow_cache[name] = glow_surface
    
    def process(self, dt: float) -> None:
        """Render all entities."""
        if not self.world:
            return
        
        # Get camera from world or use default
        camera = self._get_camera()
        screen_w, screen_h = self.screen.get_size()
        
        # Clear screen
        self.screen.fill(self.settings.COLOR_BG)
        
        # Render layers in order
        self._render_links(camera, screen_w, screen_h)
        self._render_nodes(camera, screen_w, screen_h)
        self._render_signals(camera, screen_w, screen_h)
    
    def _get_camera(self) -> Camera:
        """Get camera component or create default."""
        if self.camera:
            return self.camera
        
        # Try to find camera entity
        if self.world:
            for entity in self.world.query(Camera):
                cam = self.world.get_component(entity, Camera)
                if cam:
                    self.camera = cam
                    return cam
        
        # Default camera
        return Camera(x=self.settings.SCREEN_WIDTH // 2, 
                     y=self.settings.SCREEN_HEIGHT // 2)
    
    def _render_links(self, camera: Camera, screen_w: int, screen_h: int) -> None:
        """Render all network links with bandwidth indicators."""
        if not self.world:
            return
        
        # Collect link data for batched rendering
        link_draws: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int, int], int, float]] = []
        
        for entity, link in self.world.query_with_components(NetworkLink):
            if not link.active:
                continue
            
            # Get node positions
            pos_a = self._get_node_position(link.a)
            pos_b = self._get_node_position(link.b)
            
            if pos_a is None or pos_b is None:
                continue
            
            # Convert to screen coordinates
            screen_a = camera.world_to_screen(pos_a.x, pos_a.y, screen_w, screen_h)
            screen_b = camera.world_to_screen(pos_b.x, pos_b.y, screen_w, screen_h)
            
            # Determine color based on load
            load_ratio = link.current_load / max(link.bandwidth, 1)
            if load_ratio > 0.8:
                color = self.settings.COLOR_NODE_COMPROMISED
            elif load_ratio > 0.5:
                color = self.settings.COLOR_NODE_NEUTRAL
            else:
                color = self.settings.COLOR_LINK_DEFAULT
            
            width = max(1, int(self.settings.LINK_WIDTH * camera.zoom))
            link_draws.append((screen_a, screen_b, color, width, load_ratio))
        
        # Draw all links
        for screen_a, screen_b, color, width, load_ratio in link_draws:
            pygame.draw.line(self.screen, color, screen_a, screen_b, width)
            
            # Draw load indicator (small bar)
            if load_ratio > 0 and camera.zoom > self.lod_zoom_threshold:
                mid_x = (screen_a[0] + screen_b[0]) // 2
                mid_y = (screen_a[1] + screen_b[1]) // 2
                bar_width = int(20 * camera.zoom)
                bar_height = int(4 * camera.zoom)
                
                # Background bar
                bg_rect = pygame.Rect(mid_x - bar_width // 2, mid_y - bar_height // 2,
                                     bar_width, bar_height)
                pygame.draw.rect(self.screen, (40, 40, 50), bg_rect)
                
                # Fill bar
                fill_width = int(bar_width * min(1.0, load_ratio))
                fill_color = color
                fill_rect = pygame.Rect(mid_x - bar_width // 2, mid_y - bar_height // 2,
                                       fill_width, bar_height)
                pygame.draw.rect(self.screen, fill_color, fill_rect)
    
    def _render_nodes(self, camera: Camera, screen_w: int, screen_h: int) -> None:
        """Render all network nodes."""
        if not self.world:
            return
        
        for entity, pos, node in self.world.query_with_components(Position, NetworkNode):
            screen_pos = camera.world_to_screen(pos.x, pos.y, screen_w, screen_h)
            
            # Skip if off-screen
            margin = 50
            if (screen_pos[0] < -margin or screen_pos[0] > screen_w + margin or
                screen_pos[1] < -margin or screen_pos[1] > screen_h + margin):
                continue
            
            # Determine node state for coloring
            if node.trust > 0.7:
                state = 'trusted'
            elif node.trust < 0.3:
                state = 'compromised'
            else:
                state = 'neutral'
            
            # Draw glow if enabled and selected/hovered
            if self.settings.ENABLE_GLOW and state in self._glow_cache:
                if node.node_id == self.selected_node_id or node.node_id == self.hovered_node_id:
                    glow = self._glow_cache[state]
                    glow_rect = glow.get_rect(center=screen_pos)
                    self.screen.blit(glow, glow_rect)
            
            # Draw node
            if state in self._node_cache:
                node_surf = self._node_cache[state]
                scaled_size = int(node_surf.get_width() * camera.zoom)
                if scaled_size > 0:
                    scaled_surf = pygame.transform.scale(node_surf, (scaled_size, scaled_size))
                    rect = scaled_surf.get_rect(center=screen_pos)
                    self.screen.blit(scaled_surf, rect)
            else:
                # Fallback to simple circle
                radius = int(self.settings.NODE_RADIUS * camera.zoom)
                color = self.settings.COLOR_NODE_NEUTRAL
                pygame.draw.circle(self.screen, color, screen_pos, radius)
            
            # Draw selection highlight
            if node.node_id == self.selected_node_id:
                radius = int((self.settings.NODE_RADIUS + 5) * camera.zoom)
                pygame.draw.circle(self.screen, (255, 255, 255), screen_pos, radius, 2)
            
            # Draw node label if zoomed in enough
            if camera.zoom > self.lod_zoom_threshold and self._font:
                label = self._font.render(node.name or node.node_id, True, 
                                         self.settings.COLOR_TEXT)
                label_rect = label.get_rect(center=(screen_pos[0], 
                                                    screen_pos[1] + int(30 * camera.zoom)))
                self.screen.blit(label, label_rect)
    
    def _render_signals(self, camera: Camera, screen_w: int, screen_h: int) -> None:
        """Render signals traveling through the network."""
        if not self.world:
            return
        
        signal_count = 0
        use_simple = False
        
        # Count signals for LOD
        for _ in self.world.query(Signal):
            signal_count += 1
        
        if signal_count > self.lod_signal_threshold or camera.zoom < self.lod_zoom_threshold:
            use_simple = True
        
        for entity, signal in self.world.query_with_components(Signal):
            if signal.state not in ('traveling', 'queued'):
                continue
            
            # Calculate current position along path
            pos = self._get_signal_position(signal, camera, screen_w, screen_h)
            if pos is None:
                continue
            
            screen_pos = pos
            
            # Skip if off-screen
            margin = 20
            if (screen_pos[0] < -margin or screen_pos[0] > screen_w + margin or
                screen_pos[1] < -margin or screen_pos[1] > screen_h + margin):
                continue
            
            # Draw signal
            radius = max(2, int(self.settings.SIGNAL_RADIUS * camera.zoom))
            
            if use_simple:
                # Simple dot
                pygame.draw.circle(self.screen, self.settings.COLOR_SIGNAL, 
                                 (int(screen_pos[0]), int(screen_pos[1])), radius)
            else:
                # Fancy signal with glow
                color = self.settings.COLOR_SIGNAL
                if signal.encrypted:
                    color = (200, 100, 255)  # Purple for encrypted
                
                if self.settings.ENABLE_GLOW:
                    # Outer glow
                    for r in range(radius + 4, radius, -1):
                        alpha = int(80 * (1 - (r - radius) / 4))
                        glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*color, alpha), (r, r), r)
                        self.screen.blit(glow_surf, 
                                        (int(screen_pos[0] - r), int(screen_pos[1] - r)))
                
                pygame.draw.circle(self.screen, color,
                                 (int(screen_pos[0]), int(screen_pos[1])), radius)
    
    def _get_node_position(self, node_id: str) -> Optional[Position]:
        """Get position component for a node by ID."""
        if not self.world:
            return None
        
        for entity, pos, node in self.world.query_with_components(Position, NetworkNode):
            if node.node_id == node_id:
                return pos
        return None
    
    def _get_signal_position(self, signal: Signal, camera: Camera, 
                            screen_w: int, screen_h: int) -> Optional[Tuple[int, int]]:
        """Calculate screen position for a signal based on its path progress."""
        if not signal.path or signal.current_index >= len(signal.path) - 1:
            return None
        
        # Get current edge nodes
        current_node_id = signal.path[signal.current_index]
        next_node_id = signal.path[signal.current_index + 1]
        
        pos_a = self._get_node_position(current_node_id)
        pos_b = self._get_node_position(next_node_id)
        
        if pos_a is None or pos_b is None:
            return None
        
        # Interpolate position
        t = signal.progress
        world_x = pos_a.x + (pos_b.x - pos_a.x) * t
        world_y = pos_a.y + (pos_b.y - pos_a.y) * t
        
        return camera.world_to_screen(world_x, world_y, screen_w, screen_h)
    
    def set_selection(self, node_id: Optional[str]) -> None:
        """Set the selected node."""
        self.selected_node_id = node_id
    
    def set_hover(self, node_id: Optional[str]) -> None:
        """Set the hovered node."""
        self.hovered_node_id = node_id
