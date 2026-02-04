"""
Menu system for the game with modern UI and mouse support.
"""

import math
from typing import List, Callable, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


@dataclass
class MenuItem:
    """A single menu item."""
    text: str
    action: Optional[Callable] = None
    enabled: bool = True
    data: Any = None
    # For sliders
    is_slider: bool = False
    slider_value: float = 0.5
    slider_callback: Optional[Callable[[float], None]] = None


class MenuState(Enum):
    """Menu states."""
    MAIN = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    SETTINGS = auto()
    CONTROLS = auto()


class Menu:
    """
    Base menu class with mouse support and modern visuals.
    """
    
    BUTTON_WIDTH = 280
    BUTTON_HEIGHT = 50
    BUTTON_SPACING = 15
    BUTTON_RADIUS = 12
    
    def __init__(
        self,
        screen: pygame.Surface,
        title: str = "",
        items: List[MenuItem] = None
    ):
        """
        Initialize menu.
        
        Args:
            screen: Surface to render to
            title: Menu title
            items: List of menu items
        """
        self._screen = screen
        self._title = title
        self._items = items or []
        self._selected_index = 0
        self._hovered_index = -1
        
        # Fonts
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 56)
        self._font_item = pygame.font.Font(None, 32)
        self._font_hint = pygame.font.Font(None, 22)
        
        # Colors with gradient support
        self._bg_color = (15, 15, 25)
        self._title_color = (100, 200, 255)
        self._button_normal = (45, 45, 65)
        self._button_hover = (65, 65, 95)
        self._button_selected = (80, 80, 120)
        self._button_disabled = (35, 35, 45)
        self._text_normal = (180, 180, 200)
        self._text_hover = (255, 255, 255)
        self._text_disabled = (90, 90, 100)
        self._accent_color = (100, 180, 255)
        self._glow_color = (100, 180, 255, 50)
        
        # Animation state
        self._hover_animations: dict = {}  # index -> animation progress (0-1)
        self._title_offset = 0.0
        self._time = 0.0
        
        # Button rects for mouse detection
        self._button_rects: List[pygame.Rect] = []
        
        # Slider drag state
        self._dragging_slider: int = -1  # Index of slider being dragged, -1 = none
        
        # Audio callback
        self._play_sound: Optional[Callable[[str], None]] = None
        
        # Event callbacks
        self._on_select: Optional[Callable] = None
        self._on_back: Optional[Callable] = None
    
    def set_sound_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for playing sounds."""
        self._play_sound = callback
    
    def _play(self, sound: str) -> None:
        """Play a sound if callback is set."""
        if self._play_sound:
            self._play_sound(sound)
    
    def add_item(self, item: MenuItem) -> None:
        """Add a menu item."""
        self._items.append(item)
        self._hover_animations[len(self._items) - 1] = 0.0
    
    def clear_items(self) -> None:
        """Remove all items."""
        self._items.clear()
        self._selected_index = 0
        self._hovered_index = -1
        self._hover_animations.clear()
        self._button_rects.clear()
    
    def move_up(self) -> None:
        """Move selection up."""
        if not self._items:
            return
        
        old_index = self._selected_index
        self._selected_index = (self._selected_index - 1) % len(self._items)
        
        # Skip disabled items
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index = (self._selected_index - 1) % len(self._items)
            attempts += 1
        
        if old_index != self._selected_index:
            self._play("menu_move")
    
    def move_down(self) -> None:
        """Move selection down."""
        if not self._items:
            return
        
        old_index = self._selected_index
        self._selected_index = (self._selected_index + 1) % len(self._items)
        
        # Skip disabled items
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index = (self._selected_index + 1) % len(self._items)
            attempts += 1
        
        if old_index != self._selected_index:
            self._play("menu_move")
    
    def select(self) -> Optional[Any]:
        """
        Select current item.
        
        Returns:
            Result of item action, or item data
        """
        if not self._items:
            return None
        
        item = self._items[self._selected_index]
        if not item.enabled:
            return None
        
        self._play("menu_select")
        
        if item.action:
            return item.action()
        
        return item.data
    
    def _get_button_rect(self, index: int, width: int, height: int) -> pygame.Rect:
        """Calculate button rectangle for an item."""
        start_y = height // 2 - (len(self._items) * (self.BUTTON_HEIGHT + self.BUTTON_SPACING)) // 2 + 30
        
        x = (width - self.BUTTON_WIDTH) // 2
        y = start_y + index * (self.BUTTON_HEIGHT + self.BUTTON_SPACING)
        
        return pygame.Rect(x, y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input event including mouse.
        
        Args:
            event: Pygame event
        
        Returns:
            True if event was handled
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.move_up()
                return True
            elif event.key == pygame.K_DOWN:
                self.move_down()
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.select()
                return True
            elif event.key == pygame.K_ESCAPE:
                if self._on_back:
                    self._play("menu_select")
                    self._on_back()
                return True
            elif event.key == pygame.K_LEFT:
                # Handle slider left
                item = self._items[self._selected_index] if self._items else None
                if item and item.is_slider:
                    item.slider_value = max(0.0, item.slider_value - 0.1)
                    if item.slider_callback:
                        item.slider_callback(item.slider_value)
                    return True
            elif event.key == pygame.K_RIGHT:
                # Handle slider right
                item = self._items[self._selected_index] if self._items else None
                if item and item.is_slider:
                    item.slider_value = min(1.0, item.slider_value + 0.1)
                    if item.slider_callback:
                        item.slider_callback(item.slider_value)
                    return True
        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # Handle slider dragging
            if self._dragging_slider >= 0 and self._dragging_slider < len(self._button_rects):
                rect = self._button_rects[self._dragging_slider]
                item = self._items[self._dragging_slider]
                if item.is_slider:
                    slider_x = rect.x + 120
                    slider_width = rect.width - 140
                    click_x = mouse_pos[0] - slider_x
                    value = max(0.0, min(1.0, click_x / slider_width))
                    item.slider_value = value
                    if item.slider_callback:
                        item.slider_callback(value)
                    return True
            
            old_selected = self._selected_index
            self._hovered_index = -1
            
            for i, rect in enumerate(self._button_rects):
                if rect.collidepoint(mouse_pos):
                    self._hovered_index = i
                    if self._items[i].enabled and i != self._selected_index:
                        self._selected_index = i
                    break
            
            # Play sound only when selection actually changed
            if self._selected_index != old_selected:
                self._play("menu_move")
            
            return self._hovered_index >= 0
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                
                for i, rect in enumerate(self._button_rects):
                    if rect.collidepoint(mouse_pos) and self._items[i].enabled:
                        self._selected_index = i
                        
                        # Handle slider click - start dragging
                        if self._items[i].is_slider:
                            self._dragging_slider = i
                            # Calculate slider value from click position
                            slider_x = rect.x + 120
                            slider_width = rect.width - 140
                            click_x = mouse_pos[0] - slider_x
                            value = max(0.0, min(1.0, click_x / slider_width))
                            self._items[i].slider_value = value
                            if self._items[i].slider_callback:
                                self._items[i].slider_callback(value)
                        else:
                            self.select()
                        return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._dragging_slider = -1
        
        return False
    
    def update(self, dt: float) -> None:
        """Update menu animations."""
        self._time += dt
        
        # Animate title
        self._title_offset = math.sin(self._time * 2) * 3
        
        # Update hover animations
        for i in range(len(self._items)):
            if i not in self._hover_animations:
                self._hover_animations[i] = 0.0
            
            target = 1.0 if i == self._selected_index else 0.0
            current = self._hover_animations[i]
            
            # Smooth animation
            diff = target - current
            self._hover_animations[i] += diff * min(1.0, dt * 12)
    
    def _draw_rounded_rect(self, surface: pygame.Surface, rect: pygame.Rect, 
                          color: Tuple[int, int, int], radius: int, 
                          border_color: Tuple[int, int, int] = None,
                          glow: bool = False) -> None:
        """Draw a rounded rectangle with optional glow."""
        if glow:
            # Draw glow effect
            glow_rect = rect.inflate(8, 8)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*self._accent_color, 30), 
                           glow_surface.get_rect(), border_radius=radius + 4)
            surface.blit(glow_surface, glow_rect.topleft)
        
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        
        if border_color:
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=radius)
    
    def _draw_gradient_rect(self, surface: pygame.Surface, rect: pygame.Rect,
                           color1: Tuple[int, int, int], color2: Tuple[int, int, int],
                           radius: int) -> None:
        """Draw a rectangle with vertical gradient."""
        # Create gradient surface
        gradient = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        for y in range(rect.height):
            t = y / rect.height
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            pygame.draw.line(gradient, (r, g, b), (0, y), (rect.width, y))
        
        # Apply rounded corners mask
        mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(), border_radius=radius)
        gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        surface.blit(gradient, rect.topleft)
    
    def draw(self) -> None:
        """Draw the menu with modern visuals."""
        width = self._screen.get_width()
        height = self._screen.get_height()
        
        # Background with subtle gradient
        self._screen.fill(self._bg_color)
        
        # Draw subtle background pattern
        for i in range(0, width, 40):
            for j in range(0, height, 40):
                alpha = int(5 + math.sin(i * 0.1 + self._time) * 2 + math.cos(j * 0.1 + self._time) * 2)
                if alpha > 0:
                    pygame.draw.rect(self._screen, (25, 25, 35), (i, j, 38, 38))
        
        # Title with glow
        if self._title:
            title_y = 80 + int(self._title_offset)
            
            # Glow effect
            glow_surface = self._font_title.render(self._title, True, (*self._accent_color[:3],))
            glow_surface.set_alpha(50)
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                x = (width - glow_surface.get_width()) // 2 + dx
                self._screen.blit(glow_surface, (x, title_y + dy))
            
            # Main title
            title_surface = self._font_title.render(self._title, True, self._title_color)
            x = (width - title_surface.get_width()) // 2
            self._screen.blit(title_surface, (x, title_y))
        
        # Build button rects
        self._button_rects.clear()
        for i in range(len(self._items)):
            self._button_rects.append(self._get_button_rect(i, width, height))
        
        # Draw menu items
        for i, item in enumerate(self._items):
            rect = self._button_rects[i]
            anim = self._hover_animations.get(i, 0.0)
            is_selected = i == self._selected_index
            is_hovered = i == self._hovered_index
            
            if not item.enabled:
                bg_color = self._button_disabled
                text_color = self._text_disabled
                border_color = None
            elif is_selected:
                # Interpolate colors for animation
                bg_color = tuple(int(self._button_normal[j] + (self._button_selected[j] - self._button_normal[j]) * anim) for j in range(3))
                text_color = tuple(int(self._text_normal[j] + (self._text_hover[j] - self._text_normal[j]) * anim) for j in range(3))
                border_color = self._accent_color
            elif is_hovered:
                bg_color = self._button_hover
                text_color = self._text_hover
                border_color = None
            else:
                bg_color = self._button_normal
                text_color = self._text_normal
                border_color = None
            
            # Draw button with glow if selected
            self._draw_rounded_rect(self._screen, rect, bg_color, self.BUTTON_RADIUS, 
                                   border_color, glow=is_selected)
            
            if item.is_slider:
                # Draw slider
                label = self._font_item.render(item.text, True, text_color)
                self._screen.blit(label, (rect.x + 15, rect.y + (rect.height - label.get_height()) // 2))
                
                # Slider track
                slider_x = rect.x + 120
                slider_y = rect.y + rect.height // 2 - 4
                slider_width = rect.width - 140
                slider_height = 8
                
                track_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
                pygame.draw.rect(self._screen, (30, 30, 40), track_rect, border_radius=4)
                
                # Slider fill
                fill_width = int(slider_width * item.slider_value)
                if fill_width > 0:
                    fill_rect = pygame.Rect(slider_x, slider_y, fill_width, slider_height)
                    pygame.draw.rect(self._screen, self._accent_color, fill_rect, border_radius=4)
                
                # Slider handle - clamp to track bounds
                handle_x = max(slider_x, slider_x + fill_width - 6)
                handle_x = min(handle_x, slider_x + slider_width - 12)
                handle_rect = pygame.Rect(handle_x, slider_y - 4, 12, 16)
                pygame.draw.rect(self._screen, (220, 220, 230), handle_rect, border_radius=4)
                
                # Value text
                value_text = f"{int(item.slider_value * 100)}%"
                value_surface = self._font_hint.render(value_text, True, text_color)
                self._screen.blit(value_surface, (rect.right - 50, rect.y + (rect.height - value_surface.get_height()) // 2))
            else:
                # Draw button text centered
                text_surface = self._font_item.render(item.text, True, text_color)
                text_x = rect.x + (rect.width - text_surface.get_width()) // 2
                text_y = rect.y + (rect.height - text_surface.get_height()) // 2
                self._screen.blit(text_surface, (text_x, text_y))
    
    def on_select(self, callback: Callable) -> None:
        """Set selection callback."""
        self._on_select = callback
    
    def on_back(self, callback: Callable) -> None:
        """Set back callback."""
        self._on_back = callback
    
    @property
    def selected_index(self) -> int:
        return self._selected_index
    
    @property
    def selected_item(self) -> Optional[MenuItem]:
        if self._items:
            return self._items[self._selected_index]
        return None


class MainMenu(Menu):
    """
    Manga-style Main menu with Play hover options, Players panel, How To Play box.
    
    Layout:
    - Left: Players panel (current player, switch player)
    - Center: Play, Options, Exit buttons (Play shows submenu on hover)
    - Right: How To Play box with visual controls
    - Bottom: Tooltips appear on hover
    """
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen, "")  # No title, we'll draw custom
        
        self._on_regular_mode: Optional[Callable] = None
        self._on_story_mode: Optional[Callable] = None
        self._on_options: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        self._on_switch_player: Optional[Callable] = None
        
        # Custom state for manga-style menu
        self._play_hovered = False
        self._play_submenu_visible = False
        self._submenu_anim = 0.0
        self._submenu_selected = 0  # 0=Regular, 1=Story
        
        # Tooltip state
        self._tooltip_text = ""
        self._tooltip_visible = False
        self._tooltip_anim = 0.0
        
        # Player info (set externally)
        self._current_player_name = ""
        self._current_player_avatar = None
        self._players_list = []  # List of (name, avatar) tuples
        
        # Button positions (calculated in draw)
        self._play_btn_rect = pygame.Rect(0, 0, 0, 0)
        self._options_btn_rect = pygame.Rect(0, 0, 0, 0)
        self._exit_btn_rect = pygame.Rect(0, 0, 0, 0)
        self._regular_btn_rect = pygame.Rect(0, 0, 0, 0)
        self._story_btn_rect = pygame.Rect(0, 0, 0, 0)
        self._switch_player_rect = pygame.Rect(0, 0, 0, 0)
        
        # Decorative elements
        self._sparkles = []
        self._init_sparkles()
        
        # Tooltip definitions
        self._tooltips = {
            "play": "Choose your game mode!\nRegular for classic gameplay,\nStory for an epic adventure!",
            "options": "Customize your experience!\nChange themes, volume, and more.",
            "exit": "Exit the game.\nYour progress is automatically saved!",
            "regular": "Classic Tetris gameplay.\nClear lines, advance stages,\nand aim for high scores!",
            "story": "Coming Soon!\nEmbark on an epic puzzle\nadventure with unique characters.",
        }
        
        self._build_menu()
    
    def _init_sparkles(self) -> None:
        """Initialize decorative sparkle particles."""
        import random
        for i in range(20):
            self._sparkles.append({
                'x': random.randint(0, self._screen.get_width()),
                'y': random.randint(0, self._screen.get_height()),
                'size': random.uniform(2, 6),
                'speed': random.uniform(20, 60),
                'phase': random.uniform(0, 6.28),
                'alpha': random.randint(50, 150),
            })
    
    def _build_menu(self) -> None:
        """Build menu items - simplified for new layout."""
        self._items = []  # We handle buttons manually now
    
    def set_player_info(self, name: str, avatar=None, players_list=None) -> None:
        """Set current player info and list of all players."""
        self._current_player_name = name
        self._current_player_avatar = avatar
        if players_list:
            self._players_list = players_list
    
    def set_callbacks(
        self,
        on_regular: Callable = None,
        on_story: Callable = None,
        on_leaderboard: Callable = None,  # Now in options
        on_add_player: Callable = None,   # Now in options
        on_settings: Callable = None,
        on_quit: Callable = None,
        on_switch_player: Callable = None
    ) -> None:
        """Set menu callbacks."""
        self._on_regular_mode = on_regular
        self._on_story_mode = on_story
        self._on_options = on_settings  # Options leads to settings
        self._on_quit = on_quit
        self._on_switch_player = on_switch_player
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._play_submenu_visible:
                    self._play_submenu_visible = False
                    self._play("menu_move")
                    return True
            elif event.key in (pygame.K_UP, pygame.K_DOWN):
                if self._play_submenu_visible:
                    self._submenu_selected = 1 - self._submenu_selected
                    self._play("menu_move")
                    return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self._play_submenu_visible:
                    if self._submenu_selected == 0:
                        self._play("menu_select")
                        if self._on_regular_mode:
                            self._on_regular_mode()
                    else:
                        self._play("menu_select")
                        if self._on_story_mode:
                            self._on_story_mode()
                    return True
        
        elif event.type == pygame.MOUSEMOTION:
            pos = event.pos
            
            # Check button hovers and update tooltip
            old_tooltip = self._tooltip_text
            self._tooltip_text = ""
            self._tooltip_visible = False
            
            if self._play_btn_rect.collidepoint(pos):
                self._play_hovered = True
                self._play_submenu_visible = True
                self._tooltip_text = self._tooltips["play"]
                self._tooltip_visible = True
            else:
                if not self._regular_btn_rect.collidepoint(pos) and not self._story_btn_rect.collidepoint(pos):
                    self._play_hovered = False
                    # Keep submenu visible briefly when moving between buttons
                    if not self._play_submenu_visible:
                        pass  # Already hidden
            
            if self._options_btn_rect.collidepoint(pos):
                self._tooltip_text = self._tooltips["options"]
                self._tooltip_visible = True
            
            if self._exit_btn_rect.collidepoint(pos):
                self._tooltip_text = self._tooltips["exit"]
                self._tooltip_visible = True
            
            if self._regular_btn_rect.collidepoint(pos) and self._play_submenu_visible:
                self._submenu_selected = 0
                self._tooltip_text = self._tooltips["regular"]
                self._tooltip_visible = True
            
            if self._story_btn_rect.collidepoint(pos) and self._play_submenu_visible:
                self._submenu_selected = 1
                self._tooltip_text = self._tooltips["story"]
                self._tooltip_visible = True
            
            if old_tooltip != self._tooltip_text and self._tooltip_text:
                self._play("menu_move")
            
            return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                
                if self._regular_btn_rect.collidepoint(pos) and self._play_submenu_visible:
                    self._play("menu_select")
                    if self._on_regular_mode:
                        self._on_regular_mode()
                    return True
                
                if self._story_btn_rect.collidepoint(pos) and self._play_submenu_visible:
                    self._play("menu_select")
                    if self._on_story_mode:
                        self._on_story_mode()
                    return True
                
                if self._play_btn_rect.collidepoint(pos):
                    self._play_submenu_visible = not self._play_submenu_visible
                    self._play("menu_select")
                    return True
                
                if self._options_btn_rect.collidepoint(pos):
                    self._play("menu_select")
                    if self._on_options:
                        self._on_options()
                    return True
                
                if self._exit_btn_rect.collidepoint(pos):
                    self._play("menu_select")
                    if self._on_quit:
                        self._on_quit()
                    return True
                
                if self._switch_player_rect.collidepoint(pos):
                    self._play("menu_select")
                    if self._on_switch_player:
                        self._on_switch_player()
                    return True
                
                # Click outside submenu hides it
                if self._play_submenu_visible:
                    self._play_submenu_visible = False
        
        return False
    
    def update(self, dt: float) -> None:
        """Update menu animations."""
        self._time += dt
        
        # Update submenu animation
        target = 1.0 if self._play_submenu_visible else 0.0
        self._submenu_anim += (target - self._submenu_anim) * min(1.0, dt * 15)
        
        # Update tooltip animation
        target = 1.0 if self._tooltip_visible else 0.0
        self._tooltip_anim += (target - self._tooltip_anim) * min(1.0, dt * 12)
        
        # Update sparkles
        for s in self._sparkles:
            s['y'] -= s['speed'] * dt
            s['phase'] += dt * 3
            if s['y'] < -10:
                s['y'] = self._screen.get_height() + 10
                import random
                s['x'] = random.randint(0, self._screen.get_width())
    
    def draw(self) -> None:
        """Draw the manga-style main menu."""
        width = self._screen.get_width()
        height = self._screen.get_height()
        
        # Draw background
        self._draw_background(width, height)
        
        # Draw sparkles
        self._draw_sparkles()
        
        # Draw title
        self._draw_title(width, height)
        
        # Draw center buttons
        self._draw_center_buttons(width, height)
        
        # Draw play submenu if visible
        if self._submenu_anim > 0.01:
            self._draw_play_submenu(width, height)
        
        # Draw left panel (players)
        self._draw_players_panel(width, height)
        
        # Draw right panel (how to play)
        self._draw_how_to_play(width, height)
        
        # Draw tooltip if visible
        if self._tooltip_anim > 0.01:
            self._draw_tooltip()
    
    def _draw_background(self, width: int, height: int) -> None:
        """Draw manga-style background."""
        # Gradient background
        for y in range(height):
            progress = y / height
            r = int(18 + progress * 8)
            g = int(18 + progress * 6)
            b = int(28 + progress * 12)
            pygame.draw.line(self._screen, (r, g, b), (0, y), (width, y))
        
        # Manga-style panel pattern
        pattern_alpha = int(8 + 4 * math.sin(self._time * 1.5))
        for x in range(0, width, 50):
            for y in range(0, height, 50):
                s = pygame.Surface((48, 48), pygame.SRCALPHA)
                s.fill((30, 30, 45, pattern_alpha))
                self._screen.blit(s, (x + 1, y + 1))
    
    def _draw_sparkles(self) -> None:
        """Draw decorative sparkle particles."""
        for s in self._sparkles:
            alpha = int(s['alpha'] * (0.5 + 0.5 * math.sin(s['phase'])))
            if alpha > 10:
                size = int(s['size'] * (0.7 + 0.3 * math.sin(s['phase'])))
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 200, 255, alpha), (size, size), size)
                self._screen.blit(surf, (int(s['x']) - size, int(s['y']) - size))
    
    def _draw_title(self, width: int, height: int) -> None:
        """Draw manga-style title with glow."""
        title_y = 60 + int(math.sin(self._time * 2) * 5)
        title_text = "BLOKKUN"
        
        # Large title with multiple glow layers
        title_font = pygame.font.Font(None, 100)
        
        # Glow layers
        glow_colors = [
            (255, 150, 200, 15),
            (255, 180, 220, 25),
            (255, 200, 230, 40),
        ]
        
        for i, color in enumerate(glow_colors):
            offset = (len(glow_colors) - i) * 4
            glow = title_font.render(title_text, True, color[:3])
            glow.set_alpha(color[3])
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                x = (width - glow.get_width()) // 2 + dx
                self._screen.blit(glow, (x, title_y + dy))
        
        # Main title
        title = title_font.render(title_text, True, (255, 255, 255))
        self._screen.blit(title, ((width - title.get_width()) // 2, title_y))
        
        # Subtitle
        subtitle_font = pygame.font.Font(None, 28)
        subtitle = subtitle_font.render("A Manga Puzzle Adventure", True, (200, 180, 220))
        self._screen.blit(subtitle, ((width - subtitle.get_width()) // 2, title_y + 75))
    
    def _draw_center_buttons(self, width: int, height: int) -> None:
        """Draw the main center buttons."""
        btn_width = 240
        btn_height = 55
        btn_spacing = 20
        start_y = height // 2 - 30
        center_x = width // 2
        
        buttons = [
            ("PLAY", "play"),
            ("OPTIONS", "options"),
            ("EXIT", "exit"),
        ]
        
        for i, (text, btn_id) in enumerate(buttons):
            y = start_y + i * (btn_height + btn_spacing)
            rect = pygame.Rect(center_x - btn_width // 2, y, btn_width, btn_height)
            
            # Store rect for click detection
            if btn_id == "play":
                self._play_btn_rect = rect
            elif btn_id == "options":
                self._options_btn_rect = rect
            elif btn_id == "exit":
                self._exit_btn_rect = rect
            
            # Check hover
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = rect.collidepoint(mouse_pos)
            
            # Draw button with manga-style
            self._draw_manga_button(rect, text, is_hovered, 
                                   accent=(255, 150, 200) if btn_id == "play" else None)
    
    def _draw_manga_button(self, rect: pygame.Rect, text: str, is_hovered: bool,
                          accent: Tuple[int, int, int] = None) -> None:
        """Draw a manga-style button."""
        # Base colors
        if is_hovered:
            bg_color = (60, 50, 80)
            border_color = accent or (200, 180, 255)
        else:
            bg_color = (40, 35, 55)
            border_color = (80, 70, 100)
        
        # Glow effect on hover
        if is_hovered:
            glow_rect = rect.inflate(12, 12)
            glow = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            glow_color = accent or (200, 150, 255)
            pygame.draw.rect(glow, (*glow_color, 30), glow.get_rect(), border_radius=18)
            self._screen.blit(glow, glow_rect.topleft)
        
        # Main button
        pygame.draw.rect(self._screen, bg_color, rect, border_radius=12)
        pygame.draw.rect(self._screen, border_color, rect, 2, border_radius=12)
        
        # Text
        font = pygame.font.Font(None, 36)
        text_color = (255, 255, 255) if is_hovered else (200, 190, 220)
        text_surf = font.render(text, True, text_color)
        text_x = rect.x + (rect.width - text_surf.get_width()) // 2
        text_y = rect.y + (rect.height - text_surf.get_height()) // 2
        self._screen.blit(text_surf, (text_x, text_y))
    
    def _draw_play_submenu(self, width: int, height: int) -> None:
        """Draw the play submenu that appears on hover."""
        if self._submenu_anim < 0.01:
            return
        
        # Position next to play button
        submenu_x = self._play_btn_rect.right + 20
        submenu_y = self._play_btn_rect.top - 10
        item_width = 180
        item_height = 45
        
        # Animate slide in
        offset_x = int(30 * (1.0 - self._submenu_anim))
        alpha = int(255 * self._submenu_anim)
        
        # Draw submenu panel
        panel_rect = pygame.Rect(submenu_x + offset_x, submenu_y, item_width, item_height * 2 + 20)
        
        # Panel background
        panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (35, 30, 50, alpha), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (100, 80, 140, alpha), panel.get_rect(), 2, border_radius=10)
        self._screen.blit(panel, panel_rect.topleft)
        
        # Draw items
        items = [("Regular Mode", 0), ("Story Mode", 1)]
        for text, idx in items:
            y = submenu_y + 10 + idx * item_height + offset_x // 3
            rect = pygame.Rect(submenu_x + offset_x + 10, y, item_width - 20, item_height - 5)
            
            if idx == 0:
                self._regular_btn_rect = rect
            else:
                self._story_btn_rect = rect
            
            is_selected = self._submenu_selected == idx
            
            # Draw item
            if is_selected:
                bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(bg, (80, 60, 100, alpha), bg.get_rect(), border_radius=8)
                self._screen.blit(bg, rect.topleft)
            
            font = pygame.font.Font(None, 28)
            color_alpha = (255, 255, 255) if is_selected else (180, 170, 200)
            text_surf = font.render(text, True, color_alpha)
            text_surf.set_alpha(alpha)
            self._screen.blit(text_surf, (rect.x + 10, rect.y + (rect.height - text_surf.get_height()) // 2))
    
    def _draw_players_panel(self, width: int, height: int) -> None:
        """Draw the players panel on the left."""
        panel_x = 40
        panel_y = height // 2 - 100
        panel_width = 200
        panel_height = 220
        
        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self._screen, (30, 25, 45), panel_rect, border_radius=15)
        pygame.draw.rect(self._screen, (70, 60, 90), panel_rect, 2, border_radius=15)
        
        # Title
        font_title = pygame.font.Font(None, 26)
        title = font_title.render("PLAYER", True, (180, 160, 200))
        self._screen.blit(title, (panel_x + (panel_width - title.get_width()) // 2, panel_y + 15))
        
        # Current player avatar (larger)
        avatar_size = 70
        avatar_x = panel_x + (panel_width - avatar_size) // 2
        avatar_y = panel_y + 45
        
        # Avatar frame
        pygame.draw.circle(self._screen, (50, 45, 70), 
                          (avatar_x + avatar_size // 2, avatar_y + avatar_size // 2), 
                          avatar_size // 2 + 5)
        
        if self._current_player_avatar:
            # Draw actual avatar
            try:
                scaled = pygame.transform.smoothscale(self._current_player_avatar, (avatar_size, avatar_size))
                # Create circular mask
                mask = pygame.Surface((avatar_size, avatar_size), pygame.SRCALPHA)
                pygame.draw.circle(mask, (255, 255, 255, 255), 
                                 (avatar_size // 2, avatar_size // 2), avatar_size // 2)
                scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self._screen.blit(scaled, (avatar_x, avatar_y))
            except:
                self._draw_default_avatar(avatar_x, avatar_y, avatar_size)
        else:
            self._draw_default_avatar(avatar_x, avatar_y, avatar_size)
        
        # Accent ring
        pygame.draw.circle(self._screen, (255, 150, 200), 
                          (avatar_x + avatar_size // 2, avatar_y + avatar_size // 2), 
                          avatar_size // 2 + 3, 3)
        
        # Player name
        font_name = pygame.font.Font(None, 30)
        name = self._current_player_name or "Guest"
        name_surf = font_name.render(name, True, (255, 255, 255))
        name_x = panel_x + (panel_width - name_surf.get_width()) // 2
        self._screen.blit(name_surf, (name_x, avatar_y + avatar_size + 10))
        
        # Switch player button
        btn_y = panel_y + panel_height - 45
        self._switch_player_rect = pygame.Rect(panel_x + 15, btn_y, panel_width - 30, 30)
        
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self._switch_player_rect.collidepoint(mouse_pos)
        
        btn_color = (60, 50, 80) if is_hovered else (45, 40, 60)
        pygame.draw.rect(self._screen, btn_color, self._switch_player_rect, border_radius=8)
        
        font_btn = pygame.font.Font(None, 22)
        btn_text = font_btn.render("Switch Player", True, (180, 170, 200))
        btn_text_x = self._switch_player_rect.x + (self._switch_player_rect.width - btn_text.get_width()) // 2
        self._screen.blit(btn_text, (btn_text_x, btn_y + 7))
    
    def _draw_default_avatar(self, x: int, y: int, size: int) -> None:
        """Draw a default avatar icon."""
        pygame.draw.circle(self._screen, (70, 60, 100), (x + size // 2, y + size // 2), size // 2)
        # Simple user icon
        font = pygame.font.Font(None, size // 2)
        icon = font.render("?", True, (150, 140, 180))
        self._screen.blit(icon, (x + (size - icon.get_width()) // 2, y + (size - icon.get_height()) // 2))
    
    def _draw_how_to_play(self, width: int, height: int) -> None:
        """Draw the How To Play panel on the right."""
        panel_width = 220
        panel_height = 320
        panel_x = width - panel_width - 40
        panel_y = height // 2 - 130
        
        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self._screen, (30, 25, 45), panel_rect, border_radius=15)
        pygame.draw.rect(self._screen, (70, 60, 90), panel_rect, 2, border_radius=15)
        
        # Title
        font_title = pygame.font.Font(None, 26)
        title = font_title.render("HOW TO PLAY", True, (180, 160, 200))
        self._screen.blit(title, (panel_x + (panel_width - title.get_width()) // 2, panel_y + 15))
        
        # Controls list with visual keys
        controls = [
            ("← →", "Move"),
            ("↓", "Soft Drop"),
            ("SPACE", "Hard Drop"),
            ("↑ / W", "Rotate"),
            ("Z", "Rotate CCW"),
            ("C", "Hold"),
            ("ESC", "Pause"),
        ]
        
        font_key = pygame.font.Font(None, 22)
        font_action = pygame.font.Font(None, 20)
        
        y = panel_y + 50
        for key, action in controls:
            # Key box
            key_surf = font_key.render(key, True, (255, 255, 255))
            key_width = max(50, key_surf.get_width() + 16)
            key_rect = pygame.Rect(panel_x + 15, y, key_width, 28)
            pygame.draw.rect(self._screen, (50, 45, 70), key_rect, border_radius=6)
            pygame.draw.rect(self._screen, (90, 80, 110), key_rect, 1, border_radius=6)
            self._screen.blit(key_surf, (key_rect.x + (key_width - key_surf.get_width()) // 2, y + 6))
            
            # Action text
            action_surf = font_action.render(action, True, (170, 160, 190))
            self._screen.blit(action_surf, (panel_x + 15 + key_width + 10, y + 6))
            
            y += 36
    
    def _draw_tooltip(self) -> None:
        """Draw manga-style speech bubble tooltip."""
        if self._tooltip_anim < 0.01 or not self._tooltip_text:
            return
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Calculate tooltip size based on text
        font = pygame.font.Font(None, 22)
        lines = self._tooltip_text.split('\n')
        line_surfs = [font.render(line, True, (255, 255, 255)) for line in lines]
        
        max_width = max(s.get_width() for s in line_surfs) + 24
        total_height = len(line_surfs) * 22 + 16
        
        # Position above mouse
        tip_x = min(mouse_pos[0] + 15, self._screen.get_width() - max_width - 10)
        tip_y = max(10, mouse_pos[1] - total_height - 15)
        
        # Apply animation
        alpha = int(220 * self._tooltip_anim)
        offset_y = int(10 * (1.0 - self._tooltip_anim))
        
        tip_y += offset_y
        
        # Draw speech bubble
        bubble_rect = pygame.Rect(tip_x, tip_y, max_width, total_height)
        
        bubble = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        pygame.draw.rect(bubble, (45, 40, 65, alpha), bubble.get_rect(), border_radius=10)
        pygame.draw.rect(bubble, (120, 100, 160, alpha), bubble.get_rect(), 2, border_radius=10)
        self._screen.blit(bubble, (tip_x, tip_y))
        
        # Draw text
        for i, surf in enumerate(line_surfs):
            surf.set_alpha(alpha)
            self._screen.blit(surf, (tip_x + 12, tip_y + 8 + i * 22))


class SettingsMenu(Menu):
    """Settings menu with volume, visual options, and player management."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen, "OPTIONS")
        
        self._on_back_callback: Optional[Callable] = None
        self._on_volume_change: Optional[Callable[[str, float], None]] = None
        self._on_palette_change: Optional[Callable[[str], None]] = None
        self._on_toggle_ghost: Optional[Callable[[bool], None]] = None
        self._on_toggle_particles: Optional[Callable[[bool], None]] = None
        self._on_toggle_shake: Optional[Callable[[bool], None]] = None
        self._on_leaderboard: Optional[Callable] = None
        self._on_add_player: Optional[Callable] = None
        
        self._master_volume = 0.8
        self._sfx_volume = 0.7
        self._music_volume = 0.5
        self._current_palette = "anime"
        self._ghost_enabled = True
        self._particles_enabled = True
        self._shake_enabled = True
        
        self._build_menu()
    
    def _build_menu(self) -> None:
        """Build settings menu items."""
        self._items = [
            MenuItem("Master", is_slider=True, slider_value=self._master_volume,
                    slider_callback=lambda v: self._set_volume("master", v)),
            MenuItem("SFX", is_slider=True, slider_value=self._sfx_volume,
                    slider_callback=lambda v: self._set_volume("sfx", v)),
            MenuItem("Music", is_slider=True, slider_value=self._music_volume,
                    slider_callback=lambda v: self._set_volume("music", v)),
            MenuItem("THEME: Anime", action=self._cycle_palette),
            MenuItem("GHOST PIECE: ON", action=self._toggle_ghost),
            MenuItem("PARTICLES: ON", action=self._toggle_particles),
            MenuItem("SCREEN SHAKE: ON", action=self._toggle_shake),
            MenuItem("LEADERBOARD", action=self._show_leaderboard),
            MenuItem("ADD PLAYER", action=self._add_player),
            MenuItem("BACK", action=self._go_back),
        ]
        for i in range(len(self._items)):
            self._hover_animations[i] = 0.0
    
    def _set_volume(self, volume_type: str, value: float) -> None:
        """Set a volume value."""
        if volume_type == "master":
            self._master_volume = value
        elif volume_type == "sfx":
            self._sfx_volume = value
        elif volume_type == "music":
            self._music_volume = value
        
        if self._on_volume_change:
            self._on_volume_change(volume_type, value)
    
    def _cycle_palette(self) -> None:
        """Cycle through available palettes."""
        # Import theme order from settings
        from settings import THEME_ORDER
        palettes = THEME_ORDER
        
        try:
            idx = palettes.index(self._current_palette)
        except ValueError:
            idx = 0
        
        self._current_palette = palettes[(idx + 1) % len(palettes)]
        
        # Update button text - format nicely
        display_name = self._current_palette.replace('_', ' ').title()
        self._items[3].text = f"THEME: {display_name}"
        
        if self._on_palette_change:
            self._on_palette_change(self._current_palette)
    
    def _toggle_ghost(self) -> None:
        """Toggle ghost piece visibility."""
        self._ghost_enabled = not self._ghost_enabled
        self._items[4].text = f"GHOST PIECE: {'ON' if self._ghost_enabled else 'OFF'}"
        if self._on_toggle_ghost:
            self._on_toggle_ghost(self._ghost_enabled)
    
    def _toggle_particles(self) -> None:
        """Toggle particle effects."""
        self._particles_enabled = not self._particles_enabled
        self._items[5].text = f"PARTICLES: {'ON' if self._particles_enabled else 'OFF'}"
        if self._on_toggle_particles:
            self._on_toggle_particles(self._particles_enabled)
    
    def _toggle_shake(self) -> None:
        """Toggle screen shake."""
        self._shake_enabled = not self._shake_enabled
        self._items[6].text = f"SCREEN SHAKE: {'ON' if self._shake_enabled else 'OFF'}"
        if self._on_toggle_shake:
            self._on_toggle_shake(self._shake_enabled)
    
    def _show_leaderboard(self) -> None:
        """Show leaderboard."""
        if self._on_leaderboard:
            self._on_leaderboard()
    
    def _add_player(self) -> None:
        """Add new player."""
        if self._on_add_player:
            self._on_add_player()
    
    def _go_back(self) -> None:
        """Go back to previous menu."""
        if self._on_back_callback:
            self._on_back_callback()
    
    def set_callbacks(
        self,
        on_back: Callable = None,
        on_volume_change: Callable[[str, float], None] = None,
        on_palette_change: Callable[[str], None] = None,
        on_toggle_ghost: Callable[[bool], None] = None,
        on_toggle_particles: Callable[[bool], None] = None,
        on_toggle_shake: Callable[[bool], None] = None,
        on_leaderboard: Callable = None,
        on_add_player: Callable = None
    ) -> None:
        """Set settings callbacks."""
        self._on_back_callback = on_back
        self._on_back = on_back  # Also set parent class callback
        self._on_volume_change = on_volume_change
        self._on_palette_change = on_palette_change
        self._on_toggle_ghost = on_toggle_ghost
        self._on_toggle_particles = on_toggle_particles
        self._on_toggle_shake = on_toggle_shake
        self._on_leaderboard = on_leaderboard
        self._on_add_player = on_add_player
    
    def set_values(self, master: float, sfx: float, music: float, palette: str,
                   ghost: bool = True, particles: bool = True, shake: bool = True) -> None:
        """Set current values."""
        self._master_volume = master
        self._sfx_volume = sfx
        self._music_volume = music
        self._current_palette = palette
        self._ghost_enabled = ghost
        self._particles_enabled = particles
        self._shake_enabled = shake
        
        # Update sliders
        if len(self._items) > 0:
            self._items[0].slider_value = master
        if len(self._items) > 1:
            self._items[1].slider_value = sfx
        if len(self._items) > 2:
            self._items[2].slider_value = music
        if len(self._items) > 3:
            display_name = palette.replace('_', ' ').title()
            self._items[3].text = f"THEME: {display_name}"
        if len(self._items) > 4:
            self._items[4].text = f"GHOST PIECE: {'ON' if ghost else 'OFF'}"
        if len(self._items) > 5:
            self._items[5].text = f"PARTICLES: {'ON' if particles else 'OFF'}"
        if len(self._items) > 6:
            self._items[6].text = f"SCREEN SHAKE: {'ON' if shake else 'OFF'}"


class PauseMenu(Menu):
    """Pause menu."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen, "PAUSED")
        
        self._on_resume: Optional[Callable] = None
        self._on_restart: Optional[Callable] = None
        self._on_settings: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        
        self._build_menu()
    
    def _build_menu(self) -> None:
        """Build menu items."""
        self._items = [
            MenuItem("RESUME", self._resume),
            MenuItem("RESTART", self._restart),
            MenuItem("SETTINGS", self._settings),
            MenuItem("QUIT TO MENU", self._quit),
        ]
        for i in range(len(self._items)):
            self._hover_animations[i] = 0.0
    
    def _resume(self) -> None:
        if self._on_resume:
            self._on_resume()
    
    def _restart(self) -> None:
        if self._on_restart:
            self._on_restart()
    
    def _settings(self) -> None:
        if self._on_settings:
            self._on_settings()
    
    def _quit(self) -> None:
        if self._on_quit:
            self._on_quit()
    
    def set_callbacks(
        self,
        on_resume: Callable = None,
        on_restart: Callable = None,
        on_settings: Callable = None,
        on_quit: Callable = None
    ) -> None:
        """Set menu callbacks."""
        self._on_resume = on_resume
        self._on_restart = on_restart
        self._on_settings = on_settings
        self._on_quit = on_quit
    
    def draw(self) -> None:
        """Draw pause menu with semi-transparent background."""
        # Semi-transparent overlay with blur effect simulation
        overlay = pygame.Surface(
            (self._screen.get_width(), self._screen.get_height()),
            pygame.SRCALPHA
        )
        overlay.fill((10, 10, 20, 200))
        self._screen.blit(overlay, (0, 0))
        
        # Call parent draw for buttons
        width = self._screen.get_width()
        height = self._screen.get_height()
        
        # Title with glow
        title_y = height // 4 + int(self._title_offset)
        
        # Glow effect
        glow_surface = self._font_title.render(self._title, True, self._accent_color)
        glow_surface.set_alpha(50)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            x = (width - glow_surface.get_width()) // 2 + dx
            self._screen.blit(glow_surface, (x, title_y + dy))
        
        title_surface = self._font_title.render(self._title, True, self._title_color)
        x = (width - title_surface.get_width()) // 2
        self._screen.blit(title_surface, (x, title_y))
        
        # Build button rects
        self._button_rects.clear()
        start_y = height // 2 - 50
        for i in range(len(self._items)):
            rect = pygame.Rect(
                (width - self.BUTTON_WIDTH) // 2,
                start_y + i * (self.BUTTON_HEIGHT + self.BUTTON_SPACING),
                self.BUTTON_WIDTH,
                self.BUTTON_HEIGHT
            )
            self._button_rects.append(rect)
        
        # Draw buttons
        for i, item in enumerate(self._items):
            rect = self._button_rects[i]
            anim = self._hover_animations.get(i, 0.0)
            is_selected = i == self._selected_index
            
            if is_selected:
                bg_color = tuple(int(self._button_normal[j] + (self._button_selected[j] - self._button_normal[j]) * anim) for j in range(3))
                text_color = self._text_hover
                border_color = self._accent_color
            else:
                bg_color = self._button_normal
                text_color = self._text_normal
                border_color = None
            
            self._draw_rounded_rect(self._screen, rect, bg_color, self.BUTTON_RADIUS, 
                                   border_color, glow=is_selected)
            
            text_surface = self._font_item.render(item.text, True, text_color)
            text_x = rect.x + (rect.width - text_surface.get_width()) // 2
            text_y = rect.y + (rect.height - text_surface.get_height()) // 2
            self._screen.blit(text_surface, (text_x, text_y))


class GameOverMenu(Menu):
    """Game over menu."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen, "GAME OVER")
        
        self._final_score = 0
        self._final_lines = 0
        self._final_level = 0
        
        self._on_restart: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        
        self._build_menu()
    
    def _build_menu(self) -> None:
        """Build menu items."""
        self._items = [
            MenuItem("PLAY AGAIN", self._restart),
            MenuItem("QUIT TO MENU", self._quit),
        ]
        for i in range(len(self._items)):
            self._hover_animations[i] = 0.0
    
    def _restart(self) -> None:
        if self._on_restart:
            self._on_restart()
    
    def _quit(self) -> None:
        if self._on_quit:
            self._on_quit()
    
    def set_final_stats(self, score: int, lines: int, level: int) -> None:
        """Set final game stats to display."""
        self._final_score = score
        self._final_lines = lines
        self._final_level = level
    
    def set_callbacks(
        self,
        on_restart: Callable = None,
        on_quit: Callable = None
    ) -> None:
        """Set menu callbacks."""
        self._on_restart = on_restart
        self._on_quit = on_quit
    
    def draw(self) -> None:
        """Draw game over screen with stats."""
        # Semi-transparent overlay
        overlay = pygame.Surface(
            (self._screen.get_width(), self._screen.get_height()),
            pygame.SRCALPHA
        )
        overlay.fill((10, 10, 20, 220))
        self._screen.blit(overlay, (0, 0))
        
        width = self._screen.get_width()
        height = self._screen.get_height()
        
        # Title with red glow
        title_y = height // 5 + int(self._title_offset)
        title_color = (255, 100, 120)
        
        glow_surface = self._font_title.render(self._title, True, (255, 80, 100))
        glow_surface.set_alpha(60)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            x = (width - glow_surface.get_width()) // 2 + dx
            self._screen.blit(glow_surface, (x, title_y + dy))
        
        title_surface = self._font_title.render(self._title, True, title_color)
        x = (width - title_surface.get_width()) // 2
        self._screen.blit(title_surface, (x, title_y))
        
        # Stats with modern styling
        stats = [
            ("SCORE", f"{self._final_score:,}"),
            ("LINES", str(self._final_lines)),
            ("LEVEL", str(self._final_level)),
        ]
        
        stats_y = height // 3 + 20
        for i, (label, value) in enumerate(stats):
            # Label
            label_surface = self._font_hint.render(label, True, self._accent_color)
            value_surface = self._font_item.render(value, True, self._text_hover)
            
            total_width = label_surface.get_width() + 10 + value_surface.get_width()
            start_x = (width - total_width) // 2
            
            self._screen.blit(label_surface, (start_x, stats_y + i * 40))
            self._screen.blit(value_surface, (start_x + label_surface.get_width() + 10, stats_y + i * 40 - 5))
        
        # Build button rects
        self._button_rects.clear()
        start_y = height // 2 + 80
        for i in range(len(self._items)):
            rect = pygame.Rect(
                (width - self.BUTTON_WIDTH) // 2,
                start_y + i * (self.BUTTON_HEIGHT + self.BUTTON_SPACING),
                self.BUTTON_WIDTH,
                self.BUTTON_HEIGHT
            )
            self._button_rects.append(rect)
        
        # Draw buttons
        for i, item in enumerate(self._items):
            rect = self._button_rects[i]
            anim = self._hover_animations.get(i, 0.0)
            is_selected = i == self._selected_index
            
            if is_selected:
                bg_color = tuple(int(self._button_normal[j] + (self._button_selected[j] - self._button_normal[j]) * anim) for j in range(3))
                text_color = self._text_hover
                border_color = self._accent_color
            else:
                bg_color = self._button_normal
                text_color = self._text_normal
                border_color = None
            
            self._draw_rounded_rect(self._screen, rect, bg_color, self.BUTTON_RADIUS, 
                                   border_color, glow=is_selected)
            
            text_surface = self._font_item.render(item.text, True, text_color)
            text_x = rect.x + (rect.width - text_surface.get_width()) // 2
            text_y = rect.y + (rect.height - text_surface.get_height()) // 2
            self._screen.blit(text_surface, (text_x, text_y))
