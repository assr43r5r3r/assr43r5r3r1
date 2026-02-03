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
                        
                        # Handle slider click
                        if self._items[i].is_slider:
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
    """Main menu."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen, "TETRIS")
        
        self._on_start_game: Optional[Callable] = None
        self._on_settings: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        
        self._build_menu()
    
    def _build_menu(self) -> None:
        """Build menu items."""
        self._items = [
            MenuItem("PLAY", self._start_game),
            MenuItem("SETTINGS", self._open_settings),
            MenuItem("QUIT", self._quit_game),
        ]
        for i in range(len(self._items)):
            self._hover_animations[i] = 0.0
    
    def _start_game(self) -> None:
        if self._on_start_game:
            self._on_start_game()
    
    def _open_settings(self) -> None:
        if self._on_settings:
            self._on_settings()
    
    def _quit_game(self) -> None:
        if self._on_quit:
            self._on_quit()
    
    def set_callbacks(
        self,
        on_start: Callable = None,
        on_settings: Callable = None,
        on_quit: Callable = None
    ) -> None:
        """Set menu callbacks."""
        self._on_start_game = on_start
        self._on_settings = on_settings
        self._on_quit = on_quit


class SettingsMenu(Menu):
    """Settings menu with volume and visual options."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen, "SETTINGS")
        
        self._on_back_callback: Optional[Callable] = None
        self._on_volume_change: Optional[Callable[[str, float], None]] = None
        self._on_palette_change: Optional[Callable[[str], None]] = None
        
        self._master_volume = 0.8
        self._sfx_volume = 0.7
        self._music_volume = 0.5
        self._current_palette = "classic"
        
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
            MenuItem("THEME: CLASSIC", action=self._cycle_palette),
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
        palettes = ["classic", "neon", "pastel"]
        idx = palettes.index(self._current_palette)
        self._current_palette = palettes[(idx + 1) % len(palettes)]
        
        # Update button text
        self._items[3].text = f"THEME: {self._current_palette.upper()}"
        
        if self._on_palette_change:
            self._on_palette_change(self._current_palette)
    
    def _go_back(self) -> None:
        """Go back to previous menu."""
        if self._on_back_callback:
            self._on_back_callback()
    
    def set_callbacks(
        self,
        on_back: Callable = None,
        on_volume_change: Callable[[str, float], None] = None,
        on_palette_change: Callable[[str], None] = None
    ) -> None:
        """Set settings callbacks."""
        self._on_back_callback = on_back
        self._on_back = on_back  # Also set parent class callback
        self._on_volume_change = on_volume_change
        self._on_palette_change = on_palette_change
    
    def set_values(self, master: float, sfx: float, music: float, palette: str) -> None:
        """Set current values."""
        self._master_volume = master
        self._sfx_volume = sfx
        self._music_volume = music
        self._current_palette = palette
        
        # Update sliders
        if len(self._items) > 0:
            self._items[0].slider_value = master
        if len(self._items) > 1:
            self._items[1].slider_value = sfx
        if len(self._items) > 2:
            self._items[2].slider_value = music
        if len(self._items) > 3:
            self._items[3].text = f"THEME: {palette.upper()}"


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
