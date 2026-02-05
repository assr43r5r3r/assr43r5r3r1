"""
Main Game State for core gameplay.

Handles the main map screen, message routing, and game systems.
"""

import pygame
from typing import Optional, Dict, Any, List
from .base_state import BaseState
from ..settings import get_settings
from ..ecs.ecs_core import World, Entity
from ..ecs.components import (
    Position, Renderable, NetworkNode, NetworkLink, 
    Message, Signal, Faction, Camera
)
from ..ecs.systems import (
    RenderSystem, InputSystem, NetworkSystem,
    RoutingSystem, BandwidthSystem, SignalSystem, AISystem
)
from ..ui import UIManager, InboxWidget, InspectorPanel, RoutingPanel
from ..utils.debug import get_debug_overlay, get_game_logger
from ..data_loader import DataLoader


class GameState(BaseState):
    """
    Main gameplay state.
    
    Features:
    - Network map visualization
    - Message inbox management
    - Node inspection
    - Signal routing
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # ECS
        self.world: Optional[World] = None
        
        # Systems
        self.render_system: Optional[RenderSystem] = None
        self.input_system: Optional[InputSystem] = None
        self.network_system: Optional[NetworkSystem] = None
        self.routing_system: Optional[RoutingSystem] = None
        self.bandwidth_system: Optional[BandwidthSystem] = None
        self.signal_system: Optional[SignalSystem] = None
        self.ai_system: Optional[AISystem] = None
        
        # UI
        self.ui_manager: Optional[UIManager] = None
        self.inbox_widget: Optional[InboxWidget] = None
        self.inspector_panel: Optional[InspectorPanel] = None
        self.routing_panel: Optional[RoutingPanel] = None
        
        # Camera entity
        self.camera_entity: Optional[Entity] = None
        self.camera: Optional[Camera] = None
        
        # Game state
        self.player_tokens: int = 100
        self.current_day: int = 1
        self.game_time: float = 0.0
        self.paused: bool = False
        self.time_scale: float = 1.0
        
        # Selection
        self.selected_node_id: Optional[str] = None
        self.selected_message_id: Optional[str] = None
        
        # Routing state
        self.routing_start: Optional[str] = None
        self.routing_end: Optional[str] = None
        
        # World flags for narrative
        self.world_flags: Dict[str, Any] = {}
        
        # Debug
        self.debug_overlay = get_debug_overlay()
        self.logger = get_game_logger()
        
        # Fonts
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
    
    def startup(self, persistent: dict) -> None:
        """Initialize game state."""
        super().startup(persistent)
        
        pygame.font.init()
        self._font = pygame.font.Font(None, self.settings.FONT_SIZE_MEDIUM)
        self._small_font = pygame.font.Font(None, self.settings.FONT_SIZE_SMALL)
        
        # Initialize world
        if persistent.get('new_game') or self.world is None:
            self._init_new_game()
        elif persistent.get('load_save'):
            self._load_game()
        
        # Initialize UI
        self._init_ui()
    
    def _init_new_game(self) -> None:
        """Initialize a new game."""
        self.world = World()
        
        # Load game data
        loader = DataLoader()
        nodes_data = loader.load_nodes()
        links_data = loader.load_links()
        
        # Create camera
        screen_w, screen_h = self.app.screen.get_size()
        self.camera = Camera(x=screen_w // 2, y=screen_h // 2, zoom=1.0)
        self.camera_entity = self.world.create_entity(self.camera)
        
        # Create node entities
        for node_data in nodes_data:
            self.world.create_entity(
                Position(x=node_data.get('x', 0), y=node_data.get('y', 0)),
                Renderable(color=self.settings.COLOR_NODE_NEUTRAL),
                NetworkNode(
                    node_id=node_data.get('id', ''),
                    name=node_data.get('name', node_data.get('id', '')),
                    capacity=node_data.get('capacity', 10240),
                    trust=node_data.get('trust', 0.7),
                    owner=node_data.get('owner'),
                    node_type=node_data.get('type', 'relay')
                ),
                tags=['node']
            )
        
        # Create link entities
        for link_data in links_data:
            self.world.create_entity(
                NetworkLink(
                    a=link_data.get('a', ''),
                    b=link_data.get('b', ''),
                    bandwidth=link_data.get('bandwidth', 2048),
                    latency=link_data.get('latency', 0.1),
                    reliability=link_data.get('reliability', 0.9),
                    base_risk=link_data.get('base_risk', 0.1)
                ),
                tags=['link']
            )
        
        # Initialize systems
        self._init_systems()
        
        # Generate initial messages
        self._generate_initial_messages()
        
        # Reset game state
        self.player_tokens = self.settings.STARTING_TOKENS
        self.current_day = 1
        self.game_time = 0.0
        self.world_flags = {}
    
    def _init_systems(self) -> None:
        """Initialize ECS systems."""
        screen_size = self.app.screen.get_size()
        
        self.render_system = RenderSystem(self.app.screen)
        self.render_system.world = self.world
        self.render_system.camera = self.camera
        self.render_system.initialize()
        
        self.input_system = InputSystem(screen_size)
        self.input_system.world = self.world
        self.input_system.camera = self.camera
        self.input_system.on_node_click = self._on_node_click
        self.input_system.on_node_hover = self._on_node_hover
        self.input_system.on_node_double_click = self._on_node_double_click
        
        self.network_system = NetworkSystem()
        self.network_system.world = self.world
        
        self.routing_system = RoutingSystem()
        self.routing_system.world = self.world
        
        self.bandwidth_system = BandwidthSystem()
        self.bandwidth_system.world = self.world
        
        self.signal_system = SignalSystem()
        self.signal_system.world = self.world
        
        self.ai_system = AISystem()
        self.ai_system.world = self.world
        
        # Register event handlers
        self.world.on_event('message_delivered', self._on_message_delivered)
        self.world.on_event('message_intercepted', self._on_message_intercepted)
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        screen_w, screen_h = self.app.screen.get_size()
        
        self.ui_manager = UIManager(self.app.screen)
        
        # Inbox on the right
        inbox_x = screen_w - self.settings.INBOX_WIDTH - 10
        self.inbox_widget = InboxWidget(
            x=inbox_x, y=10,
            width=self.settings.INBOX_WIDTH,
            height=screen_h - 20
        )
        self.inbox_widget.on_message_select = self._on_message_select
        self.ui_manager.add_widget(self.inbox_widget)
        
        # Inspector on the left (hidden by default)
        self.inspector_panel = InspectorPanel(
            x=10, y=10,
            width=self.settings.INSPECTOR_WIDTH,
            height=300
        )
        self.inspector_panel.visible = False
        self.ui_manager.add_widget(self.inspector_panel)
        
        # Routing panel (hidden by default)
        self.routing_panel = RoutingPanel(
            x=screen_w // 2 - 200, y=screen_h // 2 - 150,
            width=400, height=300
        )
        self.routing_panel.visible = False
        self.routing_panel.on_route_select = self._on_route_select
        self.ui_manager.add_widget(self.routing_panel)
    
    def _generate_initial_messages(self) -> None:
        """Generate initial messages for the inbox."""
        # Sample messages for demo
        sample_messages = [
            {
                'id': 'M001',
                'origin': 'A',
                'dest': 'D',
                'tag': 'trade',
                'priority': 5,
                'size': 2048,
                'reward': 20,
                'content': 'Trade agreement documents for the eastern settlement.'
            },
            {
                'id': 'M002',
                'origin': 'B',
                'dest': 'E',
                'tag': 'med',
                'priority': 8,
                'size': 1024,
                'reward': 35,
                'content': 'Urgent medical supply request. Time sensitive!'
            },
            {
                'id': 'M003',
                'origin': 'C',
                'dest': 'F',
                'tag': 'personal',
                'priority': 3,
                'size': 512,
                'reward': 10,
                'content': 'Personal letter to family in the north.'
            }
        ]
        
        for msg_data in sample_messages:
            self.world.create_entity(
                Message(
                    msg_id=msg_data['id'],
                    origin=msg_data['origin'],
                    dest=msg_data['dest'],
                    tag=msg_data['tag'],
                    priority=msg_data['priority'],
                    size=msg_data['size'],
                    reward=msg_data['reward'],
                    content_snippet=msg_data['content']
                ),
                tags=['message', 'pending']
            )
    
    def _load_game(self) -> None:
        """Load a saved game."""
        # TODO: Implement save loading
        self._init_new_game()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle game events."""
        # Check for pause
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.change_state('menu', is_pause=True)
                return
            elif event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif event.key == pygame.K_F3:
                self.debug_overlay.toggle()
            elif event.key == pygame.K_1:
                self.time_scale = 1.0
            elif event.key == pygame.K_2:
                self.time_scale = 2.0
            elif event.key == pygame.K_3:
                self.time_scale = 4.0
        
        # UI handles events first
        if self.ui_manager and self.ui_manager.handle_event(event):
            return
        
        # Input system
        if self.input_system:
            self.input_system.add_event(event)
    
    def update(self, dt: float) -> None:
        """Update game logic."""
        self.debug_overlay.begin_frame()
        
        if self.paused:
            return
        
        scaled_dt = dt * self.time_scale
        self.game_time += scaled_dt
        
        # Update systems
        if self.input_system:
            start = self.debug_overlay.start_system_timing('Input')
            self.input_system.process(scaled_dt)
            self.debug_overlay.end_system_timing('Input', start)
        
        if self.network_system:
            start = self.debug_overlay.start_system_timing('Network')
            self.network_system.process(scaled_dt)
            self.debug_overlay.end_system_timing('Network', start)
        
        if self.routing_system:
            start = self.debug_overlay.start_system_timing('Routing')
            self.routing_system.process(scaled_dt)
            self.debug_overlay.end_system_timing('Routing', start)
        
        if self.bandwidth_system:
            start = self.debug_overlay.start_system_timing('Bandwidth')
            self.bandwidth_system.process(scaled_dt)
            self.debug_overlay.end_system_timing('Bandwidth', start)
        
        if self.signal_system:
            start = self.debug_overlay.start_system_timing('Signal')
            self.signal_system.process(scaled_dt)
            self.debug_overlay.end_system_timing('Signal', start)
        
        if self.ai_system:
            start = self.debug_overlay.start_system_timing('AI')
            self.ai_system.process(scaled_dt)
            self.debug_overlay.end_system_timing('AI', start)
        
        # Cleanup dead entities
        if self.world:
            self.world.cleanup()
        
        # Update UI
        if self.ui_manager:
            self.ui_manager.update(dt)
        
        # Update debug stats
        self._update_debug_stats()
    
    def _update_debug_stats(self) -> None:
        """Update debug overlay statistics."""
        if self.world:
            self.debug_overlay.set_stat('Entities', self.world.entity_count())
        
        if self.signal_system:
            self.debug_overlay.set_stat('Active Signals', 
                                        self.signal_system.active_signal_count)
        
        self.debug_overlay.set_stat('Tokens', self.player_tokens)
        self.debug_overlay.set_stat('Day', self.current_day)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the game."""
        # Render game world
        if self.render_system:
            start = self.debug_overlay.start_system_timing('Render')
            self.render_system.process(0)
            self.debug_overlay.end_system_timing('Render', start)
        
        # Render UI
        if self.ui_manager:
            self.ui_manager.render(screen)
        
        # Render HUD
        self._render_hud(screen)
        
        # Render debug overlay
        if self.debug_overlay.enabled and self._small_font:
            self.debug_overlay.render(screen, self._small_font, x=10, y=320)
        
        # Pause overlay
        if self.paused:
            self._render_pause_overlay(screen)
    
    def _render_hud(self, screen: pygame.Surface) -> None:
        """Render the heads-up display."""
        if not self._font:
            return
        
        screen_w, screen_h = screen.get_size()
        
        # Top bar
        top_bar_height = 30
        pygame.draw.rect(screen, self.settings.COLOR_UI_BG,
                        (0, 0, screen_w, top_bar_height))
        
        # Tokens
        tokens_text = f"Tokens: {self.player_tokens}"
        tokens_surface = self._font.render(tokens_text, True, 
                                           self.settings.COLOR_TEXT)
        screen.blit(tokens_surface, (10, 5))
        
        # Time/Day
        day_text = f"Day {self.current_day} - {int(self.game_time % 86400) // 3600:02d}:00"
        day_surface = self._font.render(day_text, True, self.settings.COLOR_TEXT)
        day_rect = day_surface.get_rect(center=(screen_w // 2, 15))
        screen.blit(day_surface, day_rect)
        
        # Time scale indicator
        if self.time_scale != 1.0:
            scale_text = f"x{self.time_scale:.0f}"
            scale_surface = self._font.render(scale_text, True, 
                                             self.settings.COLOR_NODE_NEUTRAL)
            screen.blit(scale_surface, (screen_w // 2 + 80, 5))
    
    def _render_pause_overlay(self, screen: pygame.Surface) -> None:
        """Render pause overlay."""
        screen_w, screen_h = screen.get_size()
        
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        
        if self._font:
            pause_text = "PAUSED - Press SPACE to resume"
            pause_surface = self._font.render(pause_text, True, 
                                             self.settings.COLOR_TEXT_HIGHLIGHT)
            pause_rect = pause_surface.get_rect(center=(screen_w // 2, screen_h // 2))
            screen.blit(pause_surface, pause_rect)
    
    # Event handlers
    def _on_node_click(self, node_id: str) -> None:
        """Handle node click."""
        self.selected_node_id = node_id
        
        if self.render_system:
            self.render_system.set_selection(node_id)
        
        # Update inspector
        if self.inspector_panel:
            node = self.network_system.get_node(node_id) if self.network_system else None
            if node:
                self.inspector_panel.set_node(node)
                self.inspector_panel.visible = True
        
        # Check if we're in routing mode
        if self.routing_start is not None and self.routing_end is None:
            self.routing_end = node_id
            self._show_routing_options()
    
    def _on_node_hover(self, node_id: Optional[str]) -> None:
        """Handle node hover."""
        if self.render_system:
            self.render_system.set_hover(node_id)
    
    def _on_node_double_click(self, node_id: str) -> None:
        """Handle node double-click."""
        # Start routing from this node
        if self.selected_message_id:
            self.routing_start = node_id
            self.routing_end = None
    
    def _on_message_select(self, message_id: str) -> None:
        """Handle message selection in inbox."""
        self.selected_message_id = message_id
        
        # Find message entity
        if self.world:
            for entity, msg in self.world.query_with_components(Message):
                if msg.msg_id == message_id:
                    # Set routing start to origin
                    self.routing_start = msg.origin
                    self.routing_end = msg.dest
                    self._show_routing_options()
                    break
    
    def _show_routing_options(self) -> None:
        """Show routing options panel."""
        if not self.routing_start or not self.routing_end:
            return
        
        if not self.routing_system or not self.routing_panel:
            return
        
        # Get alternative routes
        routes = self.routing_system.find_alternative_routes(
            self.routing_start, self.routing_end, k=3
        )
        
        if routes:
            self.routing_panel.set_routes(routes, self.player_tokens)
            self.routing_panel.visible = True
    
    def _on_route_select(self, route_index: int, options: Dict[str, Any]) -> None:
        """Handle route selection."""
        if not self.routing_system or route_index < 0:
            # Cancelled
            self.routing_panel.visible = False
            return
        
        routes = self.routing_system.find_alternative_routes(
            self.routing_start, self.routing_end, k=3
        )
        
        if route_index >= len(routes):
            return
        
        route = routes[route_index]
        
        # Calculate costs
        encryption_level = options.get('encryption', 0)
        cost = encryption_level * self.settings.ENCRYPTION_COST
        
        if cost > self.player_tokens:
            return  # Can't afford
        
        self.player_tokens -= cost
        
        # Find the selected message
        message_entity = None
        if self.world and self.selected_message_id:
            for entity, msg in self.world.query_with_components(Message):
                if msg.msg_id == self.selected_message_id:
                    message_entity = entity
                    break
        
        if message_entity and self.signal_system:
            # Spawn signal
            self.signal_system.spawn_signal(
                message_entity,
                route.path,
                encrypted=(encryption_level > 0)
            )
            
            # Log
            self.logger.log_message_sent(
                self.selected_message_id,
                self.routing_start,
                self.routing_end,
                route.path
            )
            
            # Remove from inbox
            message_entity.remove_tag('pending')
            message_entity.add_tag('sent')
        
        # Hide routing panel
        self.routing_panel.visible = False
        self.selected_message_id = None
        self.routing_start = None
        self.routing_end = None
    
    def _on_message_delivered(self, **kwargs) -> None:
        """Handle message delivery."""
        reward = kwargs.get('reward', 0)
        self.player_tokens += reward
        
        self.logger.log_message_delivered(
            kwargs.get('message_id', ''),
            kwargs.get('dest', ''),
            reward
        )
    
    def _on_message_intercepted(self, **kwargs) -> None:
        """Handle message interception."""
        self.logger.log_message_intercepted(
            kwargs.get('message_id', ''),
            kwargs.get('interceptor', 'unknown'),
            kwargs.get('location', '')
        )
