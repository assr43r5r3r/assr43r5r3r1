"""
Input System for handling player interactions.

Handles map interactions, node selection, camera control, and keyboard shortcuts.
"""

import pygame
from typing import Optional, Tuple, Callable, Dict, Any
from ..ecs_core import System
from ..components import Position, NetworkNode, Camera
from ...settings import get_settings


class InputSystem(System):
    """
    System for processing player input.
    
    Features:
    - Node selection and hovering
    - Camera panning and zooming
    - Keyboard shortcuts
    - Event callbacks
    """
    
    def __init__(self, screen_size: Tuple[int, int]):
        super().__init__()
        self.screen_width, self.screen_height = screen_size
        self.settings = get_settings()
        
        # Camera reference
        self.camera: Optional[Camera] = None
        
        # Input state
        self.mouse_pos: Tuple[int, int] = (0, 0)
        self.mouse_down: bool = False
        self.mouse_drag_start: Optional[Tuple[int, int]] = None
        self.camera_drag_start: Optional[Tuple[float, float]] = None
        
        # Selection state
        self.selected_node_id: Optional[str] = None
        self.hovered_node_id: Optional[str] = None
        
        # Callbacks
        self.on_node_click: Optional[Callable[[str], None]] = None
        self.on_node_hover: Optional[Callable[[Optional[str]], None]] = None
        self.on_node_double_click: Optional[Callable[[str], None]] = None
        self.on_key_press: Optional[Callable[[int], None]] = None
        
        # Key bindings
        self.key_bindings: Dict[int, str] = {
            pygame.K_ESCAPE: 'menu',
            pygame.K_i: 'inbox',
            pygame.K_r: 'route',
            pygame.K_s: 'save',
            pygame.K_d: 'debug',
            pygame.K_SPACE: 'pause',
            pygame.K_1: 'speed_normal',
            pygame.K_2: 'speed_fast',
            pygame.K_3: 'speed_faster',
        }
        
        # Double-click tracking
        self._last_click_time: float = 0
        self._last_click_node: Optional[str] = None
        self._double_click_threshold: float = 0.3  # seconds
        
        # Events to process (set by external event handling)
        self.pending_events: list = []
    
    def process(self, dt: float) -> None:
        """Process input events for this frame."""
        if not self.world:
            return
        
        camera = self._get_camera()
        
        # Process pygame events passed to us
        for event in self.pending_events:
            self._handle_event(event, camera, dt)
        
        self.pending_events.clear()
        
        # Handle continuous key presses
        self._handle_continuous_input(camera, dt)
        
        # Update hover state
        self._update_hover(camera)
    
    def add_event(self, event: pygame.event.Event) -> None:
        """Add an event to be processed."""
        self.pending_events.append(event)
    
    def _handle_event(self, event: pygame.event.Event, camera: Camera, dt: float) -> None:
        """Handle a single pygame event."""
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            
            # Handle camera drag
            if self.mouse_down and self.mouse_drag_start and self.camera_drag_start:
                dx = event.pos[0] - self.mouse_drag_start[0]
                dy = event.pos[1] - self.mouse_drag_start[1]
                camera.x = self.camera_drag_start[0] - dx / camera.zoom
                camera.y = self.camera_drag_start[1] - dy / camera.zoom
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.mouse_down = True
                self.mouse_drag_start = event.pos
                self.camera_drag_start = (camera.x, camera.y)
                
                # Check for node click
                node_id = self._get_node_at_pos(event.pos, camera)
                if node_id:
                    self._handle_node_click(node_id)
                else:
                    self.selected_node_id = None
                    
            elif event.button == 3:  # Right click
                # Could be used for context menu
                pass
                
            elif event.button == 4:  # Mouse wheel up
                self._zoom_camera(camera, 1.1, event.pos)
                
            elif event.button == 5:  # Mouse wheel down
                self._zoom_camera(camera, 0.9, event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_down = False
                self.mouse_drag_start = None
                self.camera_drag_start = None
        
        elif event.type == pygame.KEYDOWN:
            self._handle_key_press(event.key)
    
    def _handle_continuous_input(self, camera: Camera, dt: float) -> None:
        """Handle keys that are held down."""
        keys = pygame.key.get_pressed()
        
        pan_speed = self.settings.CAMERA_PAN_SPEED * dt
        
        # Camera panning with arrow keys or WASD
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            camera.x -= pan_speed / camera.zoom
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            camera.x += pan_speed / camera.zoom
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            camera.y -= pan_speed / camera.zoom
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            camera.y += pan_speed / camera.zoom
        
        # Zoom with +/-
        if keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:
            self._zoom_camera(camera, 1.0 + dt, (self.screen_width // 2, self.screen_height // 2))
        if keys[pygame.K_MINUS]:
            self._zoom_camera(camera, 1.0 - dt, (self.screen_width // 2, self.screen_height // 2))
    
    def _handle_node_click(self, node_id: str) -> None:
        """Handle clicking on a node."""
        import time
        current_time = time.time()
        
        # Check for double-click
        if (self._last_click_node == node_id and 
            current_time - self._last_click_time < self._double_click_threshold):
            # Double-click detected
            if self.on_node_double_click:
                self.on_node_double_click(node_id)
            self._last_click_node = None
            self._last_click_time = 0
        else:
            # Single click
            self.selected_node_id = node_id
            if self.on_node_click:
                self.on_node_click(node_id)
            self._last_click_node = node_id
            self._last_click_time = current_time
    
    def _handle_key_press(self, key: int) -> None:
        """Handle a key press."""
        if self.on_key_press:
            self.on_key_press(key)
        
        # Toggle debug with F3
        if key == pygame.K_F3:
            self.settings.DEBUG_OVERLAY = not self.settings.DEBUG_OVERLAY
    
    def _update_hover(self, camera: Camera) -> None:
        """Update the hovered node based on mouse position."""
        old_hover = self.hovered_node_id
        self.hovered_node_id = self._get_node_at_pos(self.mouse_pos, camera)
        
        if old_hover != self.hovered_node_id and self.on_node_hover:
            self.on_node_hover(self.hovered_node_id)
    
    def _get_node_at_pos(self, screen_pos: Tuple[int, int], camera: Camera) -> Optional[str]:
        """Get the node ID at a screen position."""
        if not self.world:
            return None
        
        world_pos = camera.screen_to_world(screen_pos[0], screen_pos[1], 
                                           self.screen_width, self.screen_height)
        
        click_radius = self.settings.NODE_RADIUS / camera.zoom + 5
        
        for entity, pos, node in self.world.query_with_components(Position, NetworkNode):
            dist = ((pos.x - world_pos[0]) ** 2 + (pos.y - world_pos[1]) ** 2) ** 0.5
            if dist < click_radius:
                return node.node_id
        
        return None
    
    def _zoom_camera(self, camera: Camera, factor: float, center: Tuple[int, int]) -> None:
        """Zoom the camera while keeping a point fixed."""
        old_zoom = camera.zoom
        camera.zoom = max(self.settings.CAMERA_ZOOM_MIN, 
                         min(self.settings.CAMERA_ZOOM_MAX, camera.zoom * factor))
        
        # Adjust camera position to zoom towards mouse
        if camera.zoom != old_zoom:
            world_before = camera.screen_to_world(center[0], center[1],
                                                  self.screen_width, self.screen_height)
            camera.zoom = camera.zoom  # Keep new zoom
            world_after = camera.screen_to_world(center[0], center[1],
                                                 self.screen_width, self.screen_height)
            
            # Adjust camera to keep the point under mouse fixed
            camera.x += world_before[0] - world_after[0]
            camera.y += world_before[1] - world_after[1]
    
    def _get_camera(self) -> Camera:
        """Get camera component or create default."""
        if self.camera:
            return self.camera
        
        if self.world:
            for entity in self.world.query(Camera):
                cam = self.world.get_component(entity, Camera)
                if cam:
                    self.camera = cam
                    return cam
        
        # Default camera
        return Camera(x=self.screen_width // 2, y=self.screen_height // 2)
    
    def get_action_for_key(self, key: int) -> Optional[str]:
        """Get the action name for a key binding."""
        return self.key_bindings.get(key)
