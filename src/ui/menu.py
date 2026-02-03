"""
Menu system for the game.
"""

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


class MenuState(Enum):
    """Menu states."""
    MAIN = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    SETTINGS = auto()
    CONTROLS = auto()


class Menu:
    """
    Base menu class.
    """
    
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
        
        # Fonts
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 64)
        self._font_item = pygame.font.Font(None, 36)
        self._font_hint = pygame.font.Font(None, 24)
        
        # Colors
        self._bg_color = (20, 20, 30)
        self._title_color = (100, 200, 255)
        self._item_color = (200, 200, 200)
        self._selected_color = (255, 255, 255)
        self._disabled_color = (100, 100, 100)
        
        # Animation
        self._selection_offset = 0.0
        
        # Event callbacks
        self._on_select: Optional[Callable] = None
        self._on_back: Optional[Callable] = None
    
    def add_item(self, item: MenuItem) -> None:
        """Add a menu item."""
        self._items.append(item)
    
    def clear_items(self) -> None:
        """Remove all items."""
        self._items.clear()
        self._selected_index = 0
    
    def move_up(self) -> None:
        """Move selection up."""
        if not self._items:
            return
        
        self._selected_index = (self._selected_index - 1) % len(self._items)
        
        # Skip disabled items
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index = (self._selected_index - 1) % len(self._items)
            attempts += 1
    
    def move_down(self) -> None:
        """Move selection down."""
        if not self._items:
            return
        
        self._selected_index = (self._selected_index + 1) % len(self._items)
        
        # Skip disabled items
        attempts = 0
        while not self._items[self._selected_index].enabled and attempts < len(self._items):
            self._selected_index = (self._selected_index + 1) % len(self._items)
            attempts += 1
    
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
        
        if item.action:
            return item.action()
        
        return item.data
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input event.
        
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
                    self._on_back()
                return True
        
        return False
    
    def update(self, dt: float) -> None:
        """Update menu animations."""
        # Animate selection indicator
        import math
        self._selection_offset = math.sin(pygame.time.get_ticks() / 200) * 5
    
    def draw(self) -> None:
        """Draw the menu."""
        width = self._screen.get_width()
        height = self._screen.get_height()
        
        # Background
        self._screen.fill(self._bg_color)
        
        # Title
        if self._title:
            title_surface = self._font_title.render(self._title, True, self._title_color)
            x = (width - title_surface.get_width()) // 2
            self._screen.blit(title_surface, (x, 80))
        
        # Menu items
        start_y = height // 2 - len(self._items) * 25
        
        for i, item in enumerate(self._items):
            is_selected = i == self._selected_index
            
            if not item.enabled:
                color = self._disabled_color
            elif is_selected:
                color = self._selected_color
            else:
                color = self._item_color
            
            text = item.text
            if is_selected:
                text = f"> {text} <"
            
            surface = self._font_item.render(text, True, color)
            x = (width - surface.get_width()) // 2
            y = start_y + i * 50
            
            if is_selected:
                x += int(self._selection_offset)
            
            self._screen.blit(surface, (x, y))
    
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
            MenuItem("START GAME", self._start_game),
            MenuItem("SETTINGS", self._open_settings),
            MenuItem("QUIT", self._quit_game),
        ]
    
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


class PauseMenu(Menu):
    """Pause menu."""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen, "PAUSED")
        
        self._on_resume: Optional[Callable] = None
        self._on_restart: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        
        self._build_menu()
    
    def _build_menu(self) -> None:
        """Build menu items."""
        self._items = [
            MenuItem("RESUME", self._resume),
            MenuItem("RESTART", self._restart),
            MenuItem("QUIT TO MENU", self._quit),
        ]
    
    def _resume(self) -> None:
        if self._on_resume:
            self._on_resume()
    
    def _restart(self) -> None:
        if self._on_restart:
            self._on_restart()
    
    def _quit(self) -> None:
        if self._on_quit:
            self._on_quit()
    
    def set_callbacks(
        self,
        on_resume: Callable = None,
        on_restart: Callable = None,
        on_quit: Callable = None
    ) -> None:
        """Set menu callbacks."""
        self._on_resume = on_resume
        self._on_restart = on_restart
        self._on_quit = on_quit
    
    def draw(self) -> None:
        """Draw pause menu with semi-transparent background."""
        # Semi-transparent overlay
        overlay = pygame.Surface(
            (self._screen.get_width(), self._screen.get_height()),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        self._screen.blit(overlay, (0, 0))
        
        # Draw menu items on top
        width = self._screen.get_width()
        height = self._screen.get_height()
        
        # Title
        title_surface = self._font_title.render(self._title, True, self._title_color)
        x = (width - title_surface.get_width()) // 2
        self._screen.blit(title_surface, (x, height // 3))
        
        # Menu items
        start_y = height // 2
        
        for i, item in enumerate(self._items):
            is_selected = i == self._selected_index
            color = self._selected_color if is_selected else self._item_color
            
            text = item.text
            if is_selected:
                text = f"> {text} <"
            
            surface = self._font_item.render(text, True, color)
            x = (width - surface.get_width()) // 2
            y = start_y + i * 50
            
            self._screen.blit(surface, (x, y))


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
        overlay.fill((0, 0, 0, 200))
        self._screen.blit(overlay, (0, 0))
        
        width = self._screen.get_width()
        height = self._screen.get_height()
        
        # Title
        title_surface = self._font_title.render(self._title, True, (255, 100, 100))
        x = (width - title_surface.get_width()) // 2
        self._screen.blit(title_surface, (x, height // 4))
        
        # Stats
        stats = [
            f"SCORE: {self._final_score:,}",
            f"LINES: {self._final_lines}",
            f"LEVEL: {self._final_level}",
        ]
        
        stats_y = height // 3 + 40
        for i, stat in enumerate(stats):
            surface = self._font_item.render(stat, True, self._item_color)
            x = (width - surface.get_width()) // 2
            self._screen.blit(surface, (x, stats_y + i * 35))
        
        # Menu items
        start_y = height // 2 + 60
        
        for i, item in enumerate(self._items):
            is_selected = i == self._selected_index
            color = self._selected_color if is_selected else self._item_color
            
            text = item.text
            if is_selected:
                text = f"> {text} <"
            
            surface = self._font_item.render(text, True, color)
            x = (width - surface.get_width()) // 2
            y = start_y + i * 50
            
            self._screen.blit(surface, (x, y))
