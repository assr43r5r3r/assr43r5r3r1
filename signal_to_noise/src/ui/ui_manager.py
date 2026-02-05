"""
UI Manager for handling UI widget rendering and input.
"""

import pygame
from typing import List, Optional, Callable
from ..settings import get_settings


class UIManager:
    """
    Manages UI widgets and their interactions.
    
    Features:
    - Widget registration and management
    - Event propagation
    - Render ordering
    """
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.settings = get_settings()
        self.widgets: List['Widget'] = []
        self.focused_widget: Optional['Widget'] = None
    
    def add_widget(self, widget: 'Widget') -> None:
        """Add a widget to the manager."""
        widget.manager = self
        self.widgets.append(widget)
    
    def remove_widget(self, widget: 'Widget') -> None:
        """Remove a widget from the manager."""
        if widget in self.widgets:
            self.widgets.remove(widget)
            if self.focused_widget == widget:
                self.focused_widget = None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle an event, propagating to widgets.
        
        Returns True if the event was consumed by a widget.
        """
        # Handle in reverse order (top widgets first)
        for widget in reversed(self.widgets):
            if not widget.visible:
                continue
            
            if widget.handle_event(event):
                return True
        
        return False
    
    def update(self, dt: float) -> None:
        """Update all widgets."""
        for widget in self.widgets:
            if widget.visible:
                widget.update(dt)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render all visible widgets."""
        for widget in self.widgets:
            if widget.visible:
                widget.render(screen)
    
    def set_focus(self, widget: 'Widget') -> None:
        """Set focus to a widget."""
        if self.focused_widget:
            self.focused_widget.on_blur()
        self.focused_widget = widget
        if widget:
            widget.on_focus()


class Widget:
    """Base class for UI widgets."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.enabled = True
        self.manager: Optional[UIManager] = None
        self.settings = get_settings()
        
        # Fonts (initialized lazily)
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
    
    @property
    def rect(self) -> pygame.Rect:
        """Get widget rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def _init_fonts(self) -> None:
        """Initialize fonts if needed."""
        if self._font is None:
            pygame.font.init()
            self._font = pygame.font.Font(None, self.settings.FONT_SIZE_MEDIUM)
            self._small_font = pygame.font.Font(None, self.settings.FONT_SIZE_SMALL)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle an event. Return True if consumed."""
        return False
    
    def update(self, dt: float) -> None:
        """Update widget state."""
        pass
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the widget."""
        pass
    
    def on_focus(self) -> None:
        """Called when widget gains focus."""
        pass
    
    def on_blur(self) -> None:
        """Called when widget loses focus."""
        pass
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within widget bounds."""
        return self.rect.collidepoint(x, y)
