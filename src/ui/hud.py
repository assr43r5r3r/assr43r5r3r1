"""
Heads-up display for in-game information.
"""

from typing import Tuple, Optional

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


class HUD:
    """
    In-game heads-up display.
    
    Shows score, level, lines, combo, and other game information.
    """
    
    def __init__(
        self,
        screen: pygame.Surface,
        font_path: Optional[str] = None
    ):
        """
        Initialize HUD.
        
        Args:
            screen: Surface to render to
            font_path: Optional path to custom font
        """
        self._screen = screen
        
        # Initialize fonts
        pygame.font.init()
        
        if font_path:
            try:
                self._font_large = pygame.font.Font(font_path, 48)
                self._font_medium = pygame.font.Font(font_path, 32)
                self._font_small = pygame.font.Font(font_path, 20)
            except:
                self._font_large = pygame.font.Font(None, 48)
                self._font_medium = pygame.font.Font(None, 32)
                self._font_small = pygame.font.Font(None, 20)
        else:
            self._font_large = pygame.font.Font(None, 48)
            self._font_medium = pygame.font.Font(None, 32)
            self._font_small = pygame.font.Font(None, 20)
        
        # Colors
        self._text_color = (255, 255, 255)
        self._accent_color = (100, 200, 255)
        self._warning_color = (255, 200, 100)
        
        # Animation state
        self._score_display = 0
        self._score_target = 0
        self._combo_display_time = 0
        self._last_combo = 0
        
        # Notification queue
        self._notifications: list = []
    
    def update(self, dt: float, score: int) -> None:
        """
        Update HUD animations.
        
        Args:
            dt: Delta time in seconds
            score: Current score
        """
        # Animate score counter
        self._score_target = score
        if self._score_display < self._score_target:
            diff = self._score_target - self._score_display
            self._score_display += max(1, int(diff * dt * 10))
            if self._score_display > self._score_target:
                self._score_display = self._score_target
        
        # Update combo display timer
        if self._combo_display_time > 0:
            self._combo_display_time -= dt
        
        # Update notifications
        self._notifications = [
            (text, time - dt) 
            for text, time in self._notifications 
            if time > dt
        ]
    
    def show_combo(self, combo: int) -> None:
        """Show combo notification."""
        self._last_combo = combo
        self._combo_display_time = 2.0
    
    def show_notification(self, text: str, duration: float = 2.0) -> None:
        """
        Show a notification.
        
        Args:
            text: Text to display
            duration: How long to show in seconds
        """
        self._notifications.append((text, duration))
    
    def draw(
        self,
        x: int,
        y: int,
        score: int,
        lines: int,
        level: int,
        combo: int = 0,
        is_back_to_back: bool = False
    ) -> None:
        """
        Draw the HUD.
        
        Args:
            x: X position
            y: Y position
            score: Current score
            lines: Lines cleared
            level: Current level
            combo: Current combo
            is_back_to_back: Whether in back-to-back state
        """
        # Draw score
        self._draw_stat(x, y, "SCORE", f"{self._score_display:,}")
        
        # Draw lines
        self._draw_stat(x, y + 60, "LINES", str(lines))
        
        # Draw level
        self._draw_stat(x, y + 120, "LEVEL", str(level))
        
        # Draw combo if active
        if self._combo_display_time > 0 and self._last_combo > 0:
            alpha = min(255, int(self._combo_display_time * 255))
            self._draw_notification(f"{self._last_combo} COMBO!", alpha)
        
        # Draw back-to-back indicator
        if is_back_to_back:
            b2b_text = self._font_small.render("BACK TO BACK", True, self._warning_color)
            self._screen.blit(b2b_text, (x, y + 180))
        
        # Draw notifications
        for i, (text, time) in enumerate(self._notifications):
            alpha = min(255, int(time * 255))
            self._draw_notification(text, alpha, offset=i * 30)
    
    def _draw_stat(self, x: int, y: int, label: str, value: str) -> None:
        """Draw a stat with label and value."""
        label_surface = self._font_small.render(label, True, self._accent_color)
        value_surface = self._font_medium.render(value, True, self._text_color)
        
        self._screen.blit(label_surface, (x, y))
        self._screen.blit(value_surface, (x, y + 20))
    
    def _draw_notification(self, text: str, alpha: int, offset: int = 0) -> None:
        """Draw a notification in the center of the screen."""
        surface = self._font_large.render(text, True, self._accent_color)
        
        # Apply alpha
        alpha_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        alpha_surface.fill((255, 255, 255, alpha))
        surface.blit(alpha_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        x = (self._screen.get_width() - surface.get_width()) // 2
        y = self._screen.get_height() // 3 + offset
        
        self._screen.blit(surface, (x, y))
    
    def set_colors(
        self,
        text: Tuple[int, int, int] = None,
        accent: Tuple[int, int, int] = None,
        warning: Tuple[int, int, int] = None
    ) -> None:
        """Set HUD colors."""
        if text:
            self._text_color = text
        if accent:
            self._accent_color = accent
        if warning:
            self._warning_color = warning
