"""
UI Widgets for the game interface.

Includes buttons, panels, inbox, inspector, and routing panels.
"""

import pygame
from typing import Optional, Callable, List, Dict, Any, Tuple
from .ui_manager import Widget
from ..settings import get_settings


class Button(Widget):
    """
    Clickable button widget.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str = "", on_click: Optional[Callable] = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.on_click = on_click
        self.hovered = False
        self.pressed = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.contains_point(*event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(*event.pos):
                self.pressed = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.pressed:
                self.pressed = False
                if self.contains_point(*event.pos) and self.on_click:
                    self.on_click()
                return True
        
        return False
    
    def render(self, screen: pygame.Surface) -> None:
        self._init_fonts()
        
        # Background color based on state
        if self.pressed:
            bg_color = (60, 60, 80)
        elif self.hovered:
            bg_color = (50, 50, 70)
        else:
            bg_color = self.settings.COLOR_UI_BG
        
        # Draw button
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER, self.rect, 2)
        
        # Draw text
        if self._font and self.text:
            text_color = self.settings.COLOR_TEXT_HIGHLIGHT if self.hovered \
                        else self.settings.COLOR_TEXT
            text_surface = self._font.render(self.text, True, text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)


class Panel(Widget):
    """
    Container panel widget.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = ""):
        super().__init__(x, y, width, height)
        self.title = title
        self.children: List[Widget] = []
    
    def add_child(self, widget: Widget) -> None:
        """Add a child widget."""
        # Offset child position relative to panel
        widget.x += self.x
        widget.y += self.y
        self.children.append(widget)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        # Check if click is within panel
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if hasattr(event, 'pos') and not self.contains_point(*event.pos):
                return False
        
        # Propagate to children
        for child in reversed(self.children):
            if child.visible and child.handle_event(event):
                return True
        
        # Consume if within panel
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(event, 'pos') and self.contains_point(*event.pos):
                return True
        
        return False
    
    def update(self, dt: float) -> None:
        for child in self.children:
            if child.visible:
                child.update(dt)
    
    def render(self, screen: pygame.Surface) -> None:
        self._init_fonts()
        
        # Background
        pygame.draw.rect(screen, self.settings.COLOR_UI_BG, self.rect)
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER, self.rect, 2)
        
        # Title
        if self.title and self._font:
            title_surface = self._font.render(self.title, True, 
                                             self.settings.COLOR_TEXT_HIGHLIGHT)
            screen.blit(title_surface, (self.x + 10, self.y + 8))
            
            # Title underline
            pygame.draw.line(screen, self.settings.COLOR_UI_BORDER,
                           (self.x + 5, self.y + 30),
                           (self.x + self.width - 5, self.y + 30))
        
        # Render children
        for child in self.children:
            if child.visible:
                child.render(screen)


class Label(Widget):
    """
    Text label widget.
    """
    
    def __init__(self, x: int, y: int, text: str = "",
                 color: Optional[Tuple[int, int, int]] = None):
        super().__init__(x, y, 0, 0)
        self.text = text
        self.color = color
    
    def render(self, screen: pygame.Surface) -> None:
        self._init_fonts()
        
        if self._font and self.text:
            color = self.color or self.settings.COLOR_TEXT
            text_surface = self._font.render(self.text, True, color)
            screen.blit(text_surface, (self.x, self.y))


class InboxWidget(Widget):
    """
    Message inbox widget.
    
    Shows list of pending messages with details.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.messages: List[Dict[str, Any]] = []
        self.selected_index: int = -1
        self.scroll_offset: int = 0
        self.on_message_select: Optional[Callable[[str], None]] = None
        
        self.item_height = 60
    
    def set_messages(self, messages: List[Dict[str, Any]]) -> None:
        """Set the list of messages to display."""
        self.messages = messages
        self.scroll_offset = 0
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the inbox."""
        self.messages.append(message)
    
    def remove_message(self, message_id: str) -> None:
        """Remove a message from the inbox."""
        self.messages = [m for m in self.messages if m.get('id') != message_id]
        if self.selected_index >= len(self.messages):
            self.selected_index = len(self.messages) - 1
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.contains_point(event.pos[0], event.pos[1]) if hasattr(event, 'pos') else False:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Check which message was clicked
                rel_y = event.pos[1] - self.y - 40 + self.scroll_offset
                clicked_index = rel_y // self.item_height
                
                if 0 <= clicked_index < len(self.messages):
                    self.selected_index = clicked_index
                    if self.on_message_select:
                        self.on_message_select(self.messages[clicked_index].get('id', ''))
                    return True
            
            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 20)
                return True
            
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self.messages) * self.item_height - (self.height - 50))
                self.scroll_offset = min(max_scroll, self.scroll_offset + 20)
                return True
        
        return False
    
    def render(self, screen: pygame.Surface) -> None:
        self._init_fonts()
        
        # Background
        pygame.draw.rect(screen, self.settings.COLOR_UI_BG, self.rect)
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER, self.rect, 2)
        
        # Title
        if self._font:
            title = f"Inbox ({len(self.messages)})"
            title_surface = self._font.render(title, True, 
                                             self.settings.COLOR_TEXT_HIGHLIGHT)
            screen.blit(title_surface, (self.x + 10, self.y + 8))
        
        # Create clip rect for messages
        clip_rect = pygame.Rect(self.x, self.y + 35, self.width, self.height - 40)
        screen.set_clip(clip_rect)
        
        # Render messages
        for i, msg in enumerate(self.messages):
            item_y = self.y + 40 + i * self.item_height - self.scroll_offset
            
            if item_y + self.item_height < clip_rect.top or item_y > clip_rect.bottom:
                continue
            
            self._render_message_item(screen, msg, i, item_y)
        
        screen.set_clip(None)
        
        # Scroll indicator
        if len(self.messages) * self.item_height > self.height - 50:
            scroll_height = max(20, (self.height - 50) * (self.height - 50) / 
                               (len(self.messages) * self.item_height))
            scroll_y = self.y + 40 + (self.height - 50 - scroll_height) * \
                       self.scroll_offset / max(1, len(self.messages) * self.item_height - self.height + 50)
            
            pygame.draw.rect(screen, (60, 60, 80),
                           (self.x + self.width - 8, int(scroll_y), 5, int(scroll_height)))
    
    def _render_message_item(self, screen: pygame.Surface, msg: Dict, 
                            index: int, y: int) -> None:
        """Render a single message item."""
        item_rect = pygame.Rect(self.x + 5, y, self.width - 15, self.item_height - 5)
        
        # Selection highlight
        if index == self.selected_index:
            pygame.draw.rect(screen, (50, 50, 70), item_rect)
        
        # Priority indicator
        priority = msg.get('priority', 5)
        if priority >= 7:
            indicator_color = self.settings.COLOR_NODE_COMPROMISED
        elif priority >= 4:
            indicator_color = self.settings.COLOR_NODE_NEUTRAL
        else:
            indicator_color = self.settings.COLOR_NODE_TRUSTED
        
        pygame.draw.rect(screen, indicator_color,
                        (self.x + 8, y + 5, 4, self.item_height - 15))
        
        if self._font and self._small_font:
            # Origin -> Dest
            route_text = f"{msg.get('origin', '?')} → {msg.get('dest', '?')}"
            route_surface = self._font.render(route_text, True, 
                                             self.settings.COLOR_TEXT)
            screen.blit(route_surface, (self.x + 20, y + 5))
            
            # Tag and size
            tag = msg.get('tag', 'unknown')
            size = msg.get('size', 0)
            info_text = f"[{tag}] {size} bytes"
            info_surface = self._small_font.render(info_text, True, (120, 120, 140))
            screen.blit(info_surface, (self.x + 20, y + 25))
            
            # Reward
            reward = msg.get('reward', 0)
            reward_text = f"+{reward}"
            reward_surface = self._small_font.render(reward_text, True, 
                                                    self.settings.COLOR_NODE_TRUSTED)
            screen.blit(reward_surface, (self.x + self.width - 50, y + 5))


class InspectorPanel(Widget):
    """
    Node inspector panel.
    
    Shows details about selected node.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.node_data: Optional[Dict[str, Any]] = None
        self.on_action: Optional[Callable[[str, str], None]] = None
        
        # Action buttons
        self.buttons: List[Button] = []
    
    def set_node(self, node) -> None:
        """Set the node to inspect."""
        if node is None:
            self.node_data = None
            return
        
        self.node_data = {
            'id': node.node_id,
            'name': node.name,
            'owner': node.owner,
            'trust': node.trust,
            'capacity': node.capacity,
            'type': node.node_type,
            'stats': node.stats.copy() if node.stats else {}
        }
        
        self._create_buttons()
    
    def _create_buttons(self) -> None:
        """Create action buttons for the node."""
        self.buttons.clear()
        
        button_y = self.y + self.height - 40
        button_width = (self.width - 30) // 2
        
        # Bribe button
        bribe_btn = Button(self.x + 10, button_y, button_width, 30,
                          "Bribe", lambda: self._on_action('bribe'))
        self.buttons.append(bribe_btn)
        
        # Inspect logs button
        logs_btn = Button(self.x + button_width + 20, button_y, button_width, 30,
                         "Logs", lambda: self._on_action('logs'))
        self.buttons.append(logs_btn)
    
    def _on_action(self, action: str) -> None:
        """Handle action button click."""
        if self.on_action and self.node_data:
            self.on_action(action, self.node_data['id'])
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        # Handle button events
        for button in self.buttons:
            if button.handle_event(event):
                return True
        
        # Consume clicks within panel
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(event, 'pos') and self.contains_point(*event.pos):
                return True
        
        return False
    
    def render(self, screen: pygame.Surface) -> None:
        if not self.visible or not self.node_data:
            return
        
        self._init_fonts()
        
        # Background
        pygame.draw.rect(screen, self.settings.COLOR_UI_BG, self.rect)
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER, self.rect, 2)
        
        # Title
        if self._font:
            title = self.node_data.get('name', 'Unknown Node')
            title_surface = self._font.render(title, True, 
                                             self.settings.COLOR_TEXT_HIGHLIGHT)
            screen.blit(title_surface, (self.x + 10, self.y + 8))
        
        # Node info
        if self._small_font:
            y_offset = 40
            info_items = [
                f"ID: {self.node_data.get('id', '?')}",
                f"Type: {self.node_data.get('type', 'relay')}",
                f"Owner: {self.node_data.get('owner') or 'Neutral'}",
                f"Trust: {self.node_data.get('trust', 0):.0%}",
                f"Capacity: {self.node_data.get('capacity', 0)} bytes"
            ]
            
            for item in info_items:
                item_surface = self._small_font.render(item, True, 
                                                      self.settings.COLOR_TEXT)
                screen.blit(item_surface, (self.x + 15, self.y + y_offset))
                y_offset += 22
            
            # Stats
            stats = self.node_data.get('stats', {})
            if stats:
                y_offset += 10
                stats_title = self._small_font.render("Statistics:", True, 
                                                     (150, 150, 170))
                screen.blit(stats_title, (self.x + 15, self.y + y_offset))
                y_offset += 20
                
                for key, value in stats.items():
                    stat_text = f"  {key}: {value}"
                    stat_surface = self._small_font.render(stat_text, True, 
                                                          (120, 120, 140))
                    screen.blit(stat_surface, (self.x + 15, self.y + y_offset))
                    y_offset += 18
        
        # Render buttons
        for button in self.buttons:
            button.render(screen)


class RoutingPanel(Widget):
    """
    Route selection panel.
    
    Shows alternative routes with metrics.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.routes: List[Any] = []
        self.selected_route: int = 0
        self.encryption_level: int = 0
        self.player_tokens: int = 0
        
        self.on_route_select: Optional[Callable[[int, Dict], None]] = None
    
    def set_routes(self, routes: List, player_tokens: int) -> None:
        """Set available routes."""
        self.routes = routes
        self.player_tokens = player_tokens
        self.selected_route = 0
        self.encryption_level = 0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_route = max(0, self.selected_route - 1)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_route = min(len(self.routes) - 1, self.selected_route + 1)
                return True
            elif event.key == pygame.K_LEFT:
                self.encryption_level = max(0, self.encryption_level - 1)
                return True
            elif event.key == pygame.K_RIGHT:
                self.encryption_level = min(3, self.encryption_level + 1)
                return True
            elif event.key == pygame.K_RETURN:
                self._confirm_route()
                return True
            elif event.key == pygame.K_ESCAPE:
                self._cancel_route()
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(*event.pos):
                # Check which route was clicked
                rel_y = event.pos[1] - self.y - 50
                clicked = rel_y // 50
                if 0 <= clicked < len(self.routes):
                    self.selected_route = clicked
                return True
        
        return self.contains_point(*event.pos) if hasattr(event, 'pos') else False
    
    def _confirm_route(self) -> None:
        """Confirm route selection."""
        if self.on_route_select:
            self.on_route_select(self.selected_route, {
                'encryption': self.encryption_level
            })
    
    def _cancel_route(self) -> None:
        """Cancel route selection."""
        if self.on_route_select:
            self.on_route_select(-1, {})
    
    def render(self, screen: pygame.Surface) -> None:
        if not self.visible:
            return
        
        self._init_fonts()
        
        # Background with slight transparency
        bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_surface.fill((30, 30, 45, 240))
        screen.blit(bg_surface, (self.x, self.y))
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER, self.rect, 2)
        
        # Title
        if self._font:
            title = "Select Route"
            title_surface = self._font.render(title, True, 
                                             self.settings.COLOR_TEXT_HIGHLIGHT)
            screen.blit(title_surface, (self.x + 10, self.y + 10))
        
        # Routes
        if self._small_font:
            for i, route in enumerate(self.routes):
                y_pos = self.y + 50 + i * 50
                
                # Selection highlight
                if i == self.selected_route:
                    pygame.draw.rect(screen, (50, 50, 70),
                                   (self.x + 5, y_pos - 2, self.width - 10, 46))
                
                # Route path
                path_str = " → ".join(route.path) if hasattr(route, 'path') else str(route)
                path_surface = self._small_font.render(path_str, True, 
                                                      self.settings.COLOR_TEXT)
                screen.blit(path_surface, (self.x + 15, y_pos))
                
                # Metrics
                if hasattr(route, 'total_latency') and hasattr(route, 'intercept_risk'):
                    metrics_text = f"Latency: {route.total_latency:.2f}s | Risk: {route.intercept_risk:.0%}"
                    metrics_surface = self._small_font.render(metrics_text, True, 
                                                             (120, 120, 140))
                    screen.blit(metrics_surface, (self.x + 15, y_pos + 18))
        
        # Encryption level
        enc_y = self.y + self.height - 80
        if self._font:
            enc_text = f"Encryption: Level {self.encryption_level}"
            enc_cost = self.encryption_level * self.settings.ENCRYPTION_COST
            cost_text = f"(Cost: {enc_cost} tokens)"
            
            enc_surface = self._font.render(enc_text, True, self.settings.COLOR_TEXT)
            screen.blit(enc_surface, (self.x + 15, enc_y))
            
            cost_color = self.settings.COLOR_NODE_TRUSTED if enc_cost <= self.player_tokens \
                        else self.settings.COLOR_NODE_COMPROMISED
            cost_surface = self._small_font.render(cost_text, True, cost_color)
            screen.blit(cost_surface, (self.x + 180, enc_y + 3))
            
            # Encryption bar
            bar_x = self.x + 15
            bar_y = enc_y + 25
            bar_width = self.width - 30
            bar_height = 8
            
            pygame.draw.rect(screen, (40, 40, 50),
                           (bar_x, bar_y, bar_width, bar_height))
            
            fill_width = int(bar_width * self.encryption_level / 3)
            if fill_width > 0:
                pygame.draw.rect(screen, (100, 150, 200),
                               (bar_x, bar_y, fill_width, bar_height))
        
        # Instructions
        if self._small_font:
            inst_text = "↑↓ Select | ←→ Encryption | Enter Confirm | Esc Cancel"
            inst_surface = self._small_font.render(inst_text, True, (80, 80, 100))
            screen.blit(inst_surface, (self.x + 10, self.y + self.height - 25))
