"""
Routing State for the routing mini-game.

Used for complex timed routing missions where player must schedule
multiple signals under strict timeline.
"""

import pygame
from typing import Optional, List, Dict, Any
from .base_state import BaseState
from ..settings import get_settings
from ..ecs.ecs_core import World
from ..ecs.components import Message, Signal


class RoutingState(BaseState):
    """
    Routing mini-game state.
    
    Features:
    - Multiple message scheduling
    - Timeline visualization
    - Strict time limits
    - Route optimization
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Mission data
        self.mission_id: str = ""
        self.time_limit: float = 60.0
        self.time_remaining: float = 60.0
        self.messages_to_route: List[Dict] = []
        self.scheduled_routes: List[Dict] = []
        
        # World reference
        self.world: Optional[World] = None
        
        # UI state
        self.selected_message_index: int = -1
        self.current_route: List[str] = []
        
        # Fonts
        self._font: Optional[pygame.font.Font] = None
        self._large_font: Optional[pygame.font.Font] = None
    
    def startup(self, persistent: dict) -> None:
        """Initialize routing state."""
        super().startup(persistent)
        
        pygame.font.init()
        self._font = pygame.font.Font(None, self.settings.FONT_SIZE_MEDIUM)
        self._large_font = pygame.font.Font(None, 36)
        
        # Get mission data from persistent
        self.mission_id = persistent.get('mission_id', 'default')
        self.time_limit = persistent.get('time_limit', 60.0)
        self.time_remaining = self.time_limit
        self.messages_to_route = persistent.get('messages', [])
        self.world = persistent.get('world')
        
        self.scheduled_routes = []
        self.selected_message_index = -1
        self.current_route = []
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle routing input."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Cancel and return to game
                self.change_state('game', routing_cancelled=True)
            elif event.key == pygame.K_RETURN:
                # Submit routing
                self._submit_routing()
            elif event.key == pygame.K_UP:
                self._select_previous_message()
            elif event.key == pygame.K_DOWN:
                self._select_next_message()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_click(event.pos)
    
    def _select_previous_message(self) -> None:
        """Select previous message in list."""
        if self.messages_to_route:
            self.selected_message_index = max(0, self.selected_message_index - 1)
    
    def _select_next_message(self) -> None:
        """Select next message in list."""
        if self.messages_to_route:
            self.selected_message_index = min(
                len(self.messages_to_route) - 1,
                self.selected_message_index + 1
            )
    
    def _handle_click(self, pos) -> None:
        """Handle mouse click."""
        # TODO: Implement click-based routing selection
        pass
    
    def _submit_routing(self) -> None:
        """Submit the routing schedule."""
        # Check if all messages are routed
        if len(self.scheduled_routes) < len(self.messages_to_route):
            return
        
        # Return to game with routing data
        self.change_state('game', 
                         routing_complete=True,
                         scheduled_routes=self.scheduled_routes)
    
    def update(self, dt: float) -> None:
        """Update routing state."""
        self.time_remaining -= dt
        
        if self.time_remaining <= 0:
            # Time's up - fail the mission
            self.change_state('game', routing_failed=True)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the routing interface."""
        screen_w, screen_h = screen.get_size()
        
        # Background
        screen.fill((20, 20, 30))
        
        # Title
        if self._large_font:
            title = f"ROUTING MISSION: {self.mission_id}"
            title_surface = self._large_font.render(title, True, 
                                                    self.settings.COLOR_TEXT_HIGHLIGHT)
            title_rect = title_surface.get_rect(center=(screen_w // 2, 30))
            screen.blit(title_surface, title_rect)
        
        # Timer
        if self._font:
            timer_color = self.settings.COLOR_TEXT
            if self.time_remaining < 10:
                timer_color = self.settings.COLOR_NODE_COMPROMISED
            
            timer_text = f"Time: {self.time_remaining:.1f}s"
            timer_surface = self._font.render(timer_text, True, timer_color)
            screen.blit(timer_surface, (screen_w - 150, 10))
        
        # Messages list
        self._render_messages_list(screen, 20, 70, 300, screen_h - 100)
        
        # Timeline/Schedule
        self._render_timeline(screen, 340, 70, screen_w - 360, screen_h - 100)
        
        # Instructions
        if self._font:
            instructions = "Arrow keys to select | Enter to submit | Escape to cancel"
            inst_surface = self._font.render(instructions, True, (100, 100, 120))
            inst_rect = inst_surface.get_rect(center=(screen_w // 2, screen_h - 20))
            screen.blit(inst_surface, inst_rect)
    
    def _render_messages_list(self, screen: pygame.Surface, 
                              x: int, y: int, width: int, height: int) -> None:
        """Render the list of messages to route."""
        # Panel background
        pygame.draw.rect(screen, self.settings.COLOR_UI_BG,
                        (x, y, width, height))
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER,
                        (x, y, width, height), 2)
        
        if not self._font:
            return
        
        # Header
        header = self._font.render("Messages", True, self.settings.COLOR_TEXT_HIGHLIGHT)
        screen.blit(header, (x + 10, y + 10))
        
        # Messages
        item_height = 40
        list_y = y + 40
        
        for i, msg_data in enumerate(self.messages_to_route):
            item_y = list_y + i * item_height
            
            # Selection highlight
            if i == self.selected_message_index:
                pygame.draw.rect(screen, (40, 40, 60),
                               (x + 5, item_y, width - 10, item_height - 5))
            
            # Check if scheduled
            is_scheduled = any(r['message_id'] == msg_data.get('id') 
                              for r in self.scheduled_routes)
            
            # Message info
            origin = msg_data.get('origin', '?')
            dest = msg_data.get('dest', '?')
            priority = msg_data.get('priority', 5)
            
            color = self.settings.COLOR_TEXT
            if is_scheduled:
                color = self.settings.COLOR_NODE_TRUSTED
            
            msg_text = f"{origin} → {dest} (P{priority})"
            msg_surface = self._font.render(msg_text, True, color)
            screen.blit(msg_surface, (x + 15, item_y + 10))
    
    def _render_timeline(self, screen: pygame.Surface,
                        x: int, y: int, width: int, height: int) -> None:
        """Render the routing timeline."""
        # Panel background
        pygame.draw.rect(screen, self.settings.COLOR_UI_BG,
                        (x, y, width, height))
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER,
                        (x, y, width, height), 2)
        
        if not self._font:
            return
        
        # Header
        header = self._font.render("Schedule", True, self.settings.COLOR_TEXT_HIGHLIGHT)
        screen.blit(header, (x + 10, y + 10))
        
        # Timeline bar
        timeline_y = y + 50
        timeline_height = 30
        pygame.draw.rect(screen, (40, 40, 50),
                        (x + 10, timeline_y, width - 20, timeline_height))
        
        # Time markers
        for t in range(0, int(self.time_limit) + 1, 10):
            marker_x = x + 10 + int((width - 20) * t / self.time_limit)
            pygame.draw.line(screen, (80, 80, 100),
                           (marker_x, timeline_y),
                           (marker_x, timeline_y + timeline_height))
            
            time_label = self._font.render(f"{t}s", True, (100, 100, 120))
            screen.blit(time_label, (marker_x - 10, timeline_y + timeline_height + 5))
        
        # Scheduled routes on timeline
        route_y = y + 100
        for i, route in enumerate(self.scheduled_routes):
            route_text = f"{route['origin']} → {route['dest']}: {' → '.join(route.get('path', []))}"
            route_surface = self._font.render(route_text, True, 
                                             self.settings.COLOR_NODE_TRUSTED)
            screen.blit(route_surface, (x + 15, route_y + i * 25))
