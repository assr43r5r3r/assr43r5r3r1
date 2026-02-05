"""
Menu State for the main menu and pause menu.
"""

import pygame
from typing import List, Tuple, Optional
from .base_state import BaseState
from ..settings import get_settings


class MenuState(BaseState):
    """
    Main menu and pause menu state.
    
    Features:
    - Title display
    - Menu options (New Game, Continue, Settings, Quit)
    - Keyboard and mouse navigation
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Menu options
        self.options: List[Tuple[str, str]] = [
            ("New Game", "new_game"),
            ("Continue", "continue"),
            ("Settings", "settings"),
            ("Quit", "quit")
        ]
        
        self.selected_index: int = 0
        self.is_pause_menu: bool = False
        
        # Fonts
        self._title_font: Optional[pygame.font.Font] = None
        self._option_font: Optional[pygame.font.Font] = None
        
        # Animation
        self._fade_alpha: float = 0.0
        self._fade_speed: float = 3.0
    
    def startup(self, persistent: dict) -> None:
        """Initialize menu state."""
        super().startup(persistent)
        
        self.is_pause_menu = persistent.get('is_pause', False)
        self._fade_alpha = 0.0
        
        # Update options for pause menu
        if self.is_pause_menu:
            self.options = [
                ("Resume", "resume"),
                ("Save Game", "save"),
                ("Settings", "settings"),
                ("Quit to Menu", "quit_to_menu")
            ]
        else:
            self.options = [
                ("New Game", "new_game"),
                ("Continue", "continue"),
                ("Settings", "settings"),
                ("Quit", "quit")
            ]
        
        # Initialize fonts
        pygame.font.init()
        self._title_font = pygame.font.Font(None, 64)
        self._option_font = pygame.font.Font(None, 36)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle menu input."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_option()
            elif event.key == pygame.K_ESCAPE:
                if self.is_pause_menu:
                    self.change_state('game')
        
        elif event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._update_hover(event.pos)
                self._select_option()
    
    def _update_hover(self, pos: Tuple[int, int]) -> None:
        """Update selected option based on mouse position."""
        screen_w, screen_h = self.app.screen.get_size()
        start_y = screen_h // 2
        
        for i, (label, _) in enumerate(self.options):
            option_y = start_y + i * 50
            option_rect = pygame.Rect(
                screen_w // 2 - 100,
                option_y - 20,
                200,
                40
            )
            if option_rect.collidepoint(pos):
                self.selected_index = i
                break
    
    def _select_option(self) -> None:
        """Execute the selected menu option."""
        if self.selected_index >= len(self.options):
            return
        
        _, action = self.options[self.selected_index]
        
        if action == "new_game":
            self.change_state('game', new_game=True)
        elif action == "continue":
            self.change_state('game', load_save=True)
        elif action == "resume":
            self.change_state('game')
        elif action == "save":
            # TODO: Trigger save
            pass
        elif action == "settings":
            # TODO: Settings state
            pass
        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif action == "quit_to_menu":
            self.is_pause_menu = False
            self.persist['is_pause'] = False
            self.startup(self.persist)
    
    def update(self, dt: float) -> None:
        """Update menu animations."""
        # Fade in
        if self._fade_alpha < 255:
            self._fade_alpha = min(255, self._fade_alpha + self._fade_speed * dt * 255)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the menu."""
        screen_w, screen_h = screen.get_size()
        
        # Background
        if self.is_pause_menu:
            # Semi-transparent overlay
            overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(self.settings.COLOR_BG)
        
        # Title
        if self._title_font:
            title_text = "SIGNAL TO NOISE"
            if self.is_pause_menu:
                title_text = "PAUSED"
            
            title_surface = self._title_font.render(
                title_text, True, self.settings.COLOR_TEXT_HIGHLIGHT
            )
            title_rect = title_surface.get_rect(center=(screen_w // 2, screen_h // 4))
            screen.blit(title_surface, title_rect)
        
        # Menu options
        if self._option_font:
            start_y = screen_h // 2
            
            for i, (label, _) in enumerate(self.options):
                color = self.settings.COLOR_TEXT
                if i == self.selected_index:
                    color = self.settings.COLOR_TEXT_HIGHLIGHT
                    # Draw selection indicator
                    indicator_x = screen_w // 2 - 120
                    indicator_y = start_y + i * 50
                    pygame.draw.polygon(screen, color, [
                        (indicator_x, indicator_y - 8),
                        (indicator_x, indicator_y + 8),
                        (indicator_x + 12, indicator_y)
                    ])
                
                option_surface = self._option_font.render(label, True, color)
                option_rect = option_surface.get_rect(
                    center=(screen_w // 2, start_y + i * 50)
                )
                screen.blit(option_surface, option_rect)
        
        # Subtitle / instructions
        if self._option_font and not self.is_pause_menu:
            subtitle = "Use arrow keys and Enter, or click to select"
            subtitle_surface = self._option_font.render(
                subtitle, True, (100, 100, 120)
            )
            subtitle_rect = subtitle_surface.get_rect(
                center=(screen_w // 2, screen_h - 50)
            )
            screen.blit(subtitle_surface, subtitle_rect)
