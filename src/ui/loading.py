"""
Loading screen with manga-style animations.
"""

import math
import random
from typing import Callable, Optional

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


class LoadingScreen:
    """
    Animated loading screen with manga/anime aesthetics.
    """
    
    def __init__(self, screen: pygame.Surface, game_name: str = "Blokkun"):
        """Initialize loading screen."""
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        self._game_name = game_name
        
        pygame.font.init()
        # Use a default font for now - in production, use a manga/comic font
        self._font_title = pygame.font.Font(None, 96)
        self._font_subtitle = pygame.font.Font(None, 36)
        self._font_loading = pygame.font.Font(None, 28)
        
        self._active = True
        self._progress = 0.0  # 0 to 1
        self._time = 0.0
        self._phase = 0  # 0=fade in, 1=loading, 2=fade out
        self._fade_alpha = 0
        
        self._on_complete: Optional[Callable] = None
        
        # Animation elements
        self._blocks = []  # Falling blocks animation
        self._init_blocks()
        
        # Loading dots animation
        self._dot_count = 0
        self._dot_timer = 0.0
    
    def _init_blocks(self) -> None:
        """Initialize decorative falling blocks."""
        colors = [
            (100, 220, 255),  # I
            (255, 230, 100),  # O
            (220, 130, 255),  # T
            (130, 255, 160),  # S
            (255, 120, 140),  # Z
            (130, 160, 255),  # J
            (255, 180, 120),  # L
        ]
        
        for i in range(12):
            self._blocks.append({
                'x': random.randint(0, self._width),
                'y': random.randint(-200, 0),
                'size': random.randint(20, 40),
                'speed': random.uniform(50, 150),
                'color': random.choice(colors),
                'rotation': random.uniform(0, 360),
                'rot_speed': random.uniform(-90, 90),
                'alpha': random.randint(30, 80),
            })
    
    def set_on_complete(self, callback: Callable) -> None:
        """Set callback when loading completes."""
        self._on_complete = callback
    
    def update(self, dt: float) -> None:
        """Update loading animation."""
        if not self._active:
            return
        
        self._time += dt
        
        # Update blocks
        for block in self._blocks:
            block['y'] += block['speed'] * dt
            block['rotation'] += block['rot_speed'] * dt
            
            # Reset block when it falls off screen
            if block['y'] > self._height + 50:
                block['y'] = -50
                block['x'] = random.randint(0, self._width)
        
        # Update loading dots
        self._dot_timer += dt
        if self._dot_timer > 0.4:
            self._dot_timer = 0.0
            self._dot_count = (self._dot_count + 1) % 4
        
        # Phase transitions
        if self._phase == 0:  # Fade in
            self._fade_alpha = min(255, self._fade_alpha + int(300 * dt))
            if self._fade_alpha >= 255:
                self._phase = 1
        
        elif self._phase == 1:  # Loading
            # Simulate loading progress
            self._progress = min(1.0, self._progress + dt * 0.5)
            
            if self._progress >= 1.0:
                self._phase = 2
        
        elif self._phase == 2:  # Fade out
            self._fade_alpha = max(0, self._fade_alpha - int(400 * dt))
            if self._fade_alpha <= 0:
                self._active = False
                if self._on_complete:
                    self._on_complete()
    
    def draw(self) -> None:
        """Draw the loading screen."""
        if not self._active:
            return
        
        # Background with gradient
        self._draw_background()
        
        # Draw falling blocks
        self._draw_blocks()
        
        # Draw title with glow
        self._draw_title()
        
        # Draw loading bar
        self._draw_loading_bar()
        
        # Draw loading text
        self._draw_loading_text()
        
        # Apply fade
        if self._fade_alpha < 255:
            overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 255 - self._fade_alpha))
            self._screen.blit(overlay, (0, 0))
    
    def _draw_background(self) -> None:
        """Draw gradient background."""
        # Dark gradient background
        for y in range(self._height):
            progress = y / self._height
            r = int(15 + progress * 10)
            g = int(15 + progress * 8)
            b = int(25 + progress * 15)
            pygame.draw.line(self._screen, (r, g, b), (0, y), (self._width, y))
        
        # Subtle pattern overlay
        pattern_alpha = int(10 + 5 * math.sin(self._time * 2))
        for x in range(0, self._width, 30):
            for y in range(0, self._height, 30):
                rect = pygame.Rect(x + 2, y + 2, 26, 26)
                s = pygame.Surface((26, 26), pygame.SRCALPHA)
                s.fill((30, 30, 45, pattern_alpha))
                self._screen.blit(s, (x + 2, y + 2))
    
    def _draw_blocks(self) -> None:
        """Draw decorative falling blocks."""
        for block in self._blocks:
            size = block['size']
            x, y = int(block['x']), int(block['y'])
            
            # Create rotated block surface
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            color = (*block['color'], block['alpha'])
            pygame.draw.rect(s, color, s.get_rect(), border_radius=4)
            
            # Add highlight
            highlight = (*[min(255, c + 40) for c in block['color']], block['alpha'] // 2)
            pygame.draw.line(s, highlight, (2, 2), (size - 2, 2), 2)
            
            # Rotate and draw
            rotated = pygame.transform.rotate(s, block['rotation'])
            rect = rotated.get_rect(center=(x, y))
            self._screen.blit(rotated, rect)
    
    def _draw_title(self) -> None:
        """Draw game title with glow effect."""
        # Calculate title position with subtle animation
        title_y = self._height // 3 + int(math.sin(self._time * 2) * 5)
        
        # Draw glow layers
        glow_colors = [
            (255, 150, 200, 20),
            (255, 180, 220, 30),
            (255, 200, 230, 40),
        ]
        
        title_text = self._game_name.upper()
        title_surf = self._font_title.render(title_text, True, (255, 255, 255))
        title_x = (self._width - title_surf.get_width()) // 2
        
        # Draw glow
        for i, color in enumerate(glow_colors):
            offset = (len(glow_colors) - i) * 3
            glow_surf = self._font_title.render(title_text, True, color[:3])
            glow_surf.set_alpha(color[3])
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                self._screen.blit(glow_surf, (title_x + dx, title_y + dy))
        
        # Draw main title
        self._screen.blit(title_surf, (title_x, title_y))
        
        # Draw subtitle
        subtitle_text = "A Manga Puzzle Adventure"
        subtitle_surf = self._font_subtitle.render(subtitle_text, True, (200, 180, 220))
        subtitle_x = (self._width - subtitle_surf.get_width()) // 2
        self._screen.blit(subtitle_surf, (subtitle_x, title_y + 80))
    
    def _draw_loading_bar(self) -> None:
        """Draw loading progress bar."""
        bar_width = 400
        bar_height = 12
        bar_x = (self._width - bar_width) // 2
        bar_y = self._height * 2 // 3
        
        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self._screen, (40, 35, 55), bg_rect, border_radius=6)
        
        # Progress fill with gradient effect
        fill_width = int(bar_width * self._progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            
            # Create gradient
            gradient = pygame.Surface((fill_width, bar_height), pygame.SRCALPHA)
            for x in range(fill_width):
                progress = x / bar_width
                r = int(255 - progress * 55)
                g = int(150 + progress * 30)
                b = int(200 + progress * 20)
                pygame.draw.line(gradient, (r, g, b), (x, 0), (x, bar_height))
            
            # Apply rounded corners
            mask = pygame.Surface((fill_width, bar_height), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(), border_radius=6)
            gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            self._screen.blit(gradient, (bar_x, bar_y))
        
        # Border
        pygame.draw.rect(self._screen, (80, 70, 100), bg_rect, 2, border_radius=6)
        
        # Shine effect
        shine_x = bar_x + int(self._time * 100) % (bar_width + 100) - 50
        if bar_x < shine_x < bar_x + fill_width:
            shine = pygame.Surface((30, bar_height), pygame.SRCALPHA)
            for x in range(30):
                alpha = int(50 * math.sin(x / 30 * math.pi))
                pygame.draw.line(shine, (255, 255, 255, alpha), (x, 0), (x, bar_height))
            self._screen.blit(shine, (shine_x, bar_y))
    
    def _draw_loading_text(self) -> None:
        """Draw loading text with animated dots."""
        dots = "." * self._dot_count
        text = f"Loading{dots}"
        text_surf = self._font_loading.render(text, True, (180, 170, 200))
        text_x = (self._width - 100) // 2
        text_y = self._height * 2 // 3 + 30
        self._screen.blit(text_surf, (text_x, text_y))
        
        # Percentage
        percent = f"{int(self._progress * 100)}%"
        percent_surf = self._font_loading.render(percent, True, (200, 190, 220))
        percent_x = (self._width - percent_surf.get_width()) // 2
        self._screen.blit(percent_surf, (percent_x, text_y + 25))
    
    def skip(self) -> None:
        """Skip the loading screen."""
        self._progress = 1.0
        self._phase = 2
    
    @property
    def is_active(self) -> bool:
        return self._active
    
    @property
    def is_complete(self) -> bool:
        return not self._active
