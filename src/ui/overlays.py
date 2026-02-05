"""
Countdown animation for game start.
"""

import math
from typing import Optional, Callable, Tuple

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


class Countdown:
    """
    Animated countdown before game starts.
    Displays "3..2..1..GO!" with modern racing-style animation.
    """
    
    COUNTDOWN_DURATION = 0.8  # Seconds per number
    GO_DURATION = 0.6  # Duration for "GO!"
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize countdown.
        
        Args:
            screen: Surface to render to
        """
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        # Fonts
        pygame.font.init()
        self._font_number = pygame.font.Font(None, 200)
        self._font_go = pygame.font.Font(None, 180)
        
        # State
        self._active = False
        self._current_number = 3
        self._timer = 0.0
        self._phase = "countdown"  # "countdown" or "go"
        
        # Animation
        self._scale = 1.0
        self._alpha = 255
        self._glow_pulse = 0.0
        
        # Callback when finished
        self._on_complete: Optional[Callable] = None
        
        # Audio callback
        self._play_sound: Optional[Callable[[str], None]] = None
        
        # Colors
        self._number_color = (255, 255, 255)
        self._go_color = (100, 255, 150)
        self._glow_color = (100, 200, 255)
    
    def set_sound_callback(self, callback: Callable[[str], None]) -> None:
        """Set sound callback."""
        self._play_sound = callback
    
    def set_on_complete(self, callback: Callable) -> None:
        """Set callback for when countdown completes."""
        self._on_complete = callback
    
    def start(self) -> None:
        """Start the countdown."""
        self._active = True
        self._current_number = 3
        self._timer = 0.0
        self._phase = "countdown"
        self._scale = 1.5
        self._alpha = 255
        
        if self._play_sound:
            self._play_sound("countdown")
    
    def stop(self) -> None:
        """Stop the countdown."""
        self._active = False
    
    def update(self, dt: float) -> bool:
        """
        Update countdown animation.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if countdown is still active
        """
        if not self._active:
            return False
        
        self._timer += dt
        self._glow_pulse += dt * 6.0
        
        if self._phase == "countdown":
            # Each number animation
            phase_progress = self._timer / self.COUNTDOWN_DURATION
            
            if phase_progress < 0.2:
                # Pop in
                t = phase_progress / 0.2
                self._scale = 1.5 - 0.5 * self._ease_out_back(t)
                self._alpha = int(255 * t)
            elif phase_progress < 0.8:
                # Hold
                self._scale = 1.0
                self._alpha = 255
            else:
                # Fade and shrink
                t = (phase_progress - 0.8) / 0.2
                self._scale = 1.0 - 0.3 * t
                self._alpha = int(255 * (1 - t))
            
            # Move to next number
            if self._timer >= self.COUNTDOWN_DURATION:
                self._timer = 0.0
                self._current_number -= 1
                
                if self._current_number <= 0:
                    self._phase = "go"
                    if self._play_sound:
                        self._play_sound("go")
                elif self._play_sound:
                    self._play_sound("countdown")
        
        elif self._phase == "go":
            phase_progress = self._timer / self.GO_DURATION
            
            if phase_progress < 0.3:
                # Burst in
                t = phase_progress / 0.3
                self._scale = 2.0 - 1.0 * self._ease_out_elastic(t)
                self._alpha = int(255 * min(1.0, t * 3))
            elif phase_progress < 0.7:
                # Hold with pulse
                self._scale = 1.0 + 0.1 * math.sin(self._glow_pulse * 3)
                self._alpha = 255
            else:
                # Zoom out and fade
                t = (phase_progress - 0.7) / 0.3
                self._scale = 1.0 + 0.5 * t
                self._alpha = int(255 * (1 - t))
            
            if self._timer >= self.GO_DURATION:
                self._active = False
                if self._on_complete:
                    self._on_complete()
        
        return self._active
    
    def _ease_out_back(self, t: float) -> float:
        """Ease out back function."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    def _ease_out_elastic(self, t: float) -> float:
        """Ease out elastic function."""
        if t == 0 or t == 1:
            return t
        c4 = (2 * math.pi) / 3
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    
    def draw(self) -> None:
        """Draw the countdown."""
        if not self._active:
            return
        
        # Determine text
        if self._phase == "countdown":
            text = str(self._current_number)
            font = self._font_number
            base_color = self._number_color
        else:
            text = "GO!"
            font = self._font_go
            base_color = self._go_color
        
        # Create glow effect
        glow_intensity = 0.5 + 0.3 * math.sin(self._glow_pulse)
        glow_size = int(8 * self._scale * glow_intensity)
        
        # Render text
        rendered = font.render(text, True, base_color)
        
        # Scale
        if self._scale != 1.0:
            new_width = int(rendered.get_width() * self._scale)
            new_height = int(rendered.get_height() * self._scale)
            if new_width > 0 and new_height > 0:
                rendered = pygame.transform.smoothscale(rendered, (new_width, new_height))
        
        # Apply alpha
        rendered.set_alpha(self._alpha)
        
        # Draw glow layers
        if glow_size > 0 and self._alpha > 100:
            glow_alpha = int((self._alpha / 255) * 60 * glow_intensity)
            glow_surf = font.render(text, True, self._glow_color)
            if self._scale != 1.0:
                glow_w = int(glow_surf.get_width() * self._scale)
                glow_h = int(glow_surf.get_height() * self._scale)
                if glow_w > 0 and glow_h > 0:
                    glow_surf = pygame.transform.smoothscale(glow_surf, (glow_w, glow_h))
            glow_surf.set_alpha(glow_alpha)
            
            # Draw multiple glow layers
            center_x = (self._width - rendered.get_width()) // 2
            center_y = (self._height - rendered.get_height()) // 2
            
            for offset in [4, 8, 12]:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    self._screen.blit(
                        glow_surf,
                        (center_x + dx * offset, center_y + dy * offset)
                    )
        
        # Draw main text
        center_x = (self._width - rendered.get_width()) // 2
        center_y = (self._height - rendered.get_height()) // 2
        self._screen.blit(rendered, (center_x, center_y))
    
    @property
    def is_active(self) -> bool:
        """Check if countdown is active."""
        return self._active


class StageTransition:
    """
    Animated transition between stages.
    """
    
    TRANSITION_DURATION = 1.5  # Seconds
    
    def __init__(self, screen: pygame.Surface):
        """Initialize transition."""
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        pygame.font.init()
        self._font_stage = pygame.font.Font(None, 80)
        self._font_name = pygame.font.Font(None, 50)
        
        self._active = False
        self._timer = 0.0
        self._stage_number = 1
        self._stage_name = ""
        
        self._on_complete: Optional[Callable] = None
        self._play_sound: Optional[Callable[[str], None]] = None
    
    def set_sound_callback(self, callback: Callable[[str], None]) -> None:
        self._play_sound = callback
    
    def set_on_complete(self, callback: Callable) -> None:
        self._on_complete = callback
    
    def start(self, stage_number: int, stage_name: str) -> None:
        """Start transition to new stage."""
        self._active = True
        self._timer = 0.0
        self._stage_number = stage_number
        self._stage_name = stage_name
        
        if self._play_sound:
            self._play_sound("stage_up")
    
    def update(self, dt: float) -> bool:
        """Update transition."""
        if not self._active:
            return False
        
        self._timer += dt
        
        if self._timer >= self.TRANSITION_DURATION:
            self._active = False
            if self._on_complete:
                self._on_complete()
            return False
        
        return True
    
    def draw(self) -> None:
        """Draw stage transition."""
        if not self._active:
            return
        
        progress = self._timer / self.TRANSITION_DURATION
        
        # Calculate animation phases
        if progress < 0.2:
            # Slide in from right
            t = progress / 0.2
            slide_x = int(self._width * (1 - self._ease_out_expo(t)))
            alpha = int(255 * t)
        elif progress < 0.7:
            # Hold
            slide_x = 0
            alpha = 255
        else:
            # Slide out to left
            t = (progress - 0.7) / 0.3
            slide_x = int(-self._width * 0.5 * self._ease_in_expo(t))
            alpha = int(255 * (1 - t))
        
        # Draw banner background
        banner_height = 150
        banner_y = (self._height - banner_height) // 2
        
        banner = pygame.Surface((self._width, banner_height), pygame.SRCALPHA)
        banner.fill((20, 20, 40, int(200 * (alpha / 255))))
        
        # Draw gradient edges
        for i in range(30):
            edge_alpha = int(200 * (1 - i / 30) * (alpha / 255))
            pygame.draw.line(
                banner, (20, 20, 40, edge_alpha),
                (0, i), (self._width, i)
            )
            pygame.draw.line(
                banner, (20, 20, 40, edge_alpha),
                (0, banner_height - 1 - i), (self._width, banner_height - 1 - i)
            )
        
        self._screen.blit(banner, (slide_x, banner_y))
        
        # Draw stage text
        stage_text = f"STAGE {self._stage_number}"
        stage_surf = self._font_stage.render(stage_text, True, (255, 220, 100))
        stage_surf.set_alpha(alpha)
        
        name_surf = self._font_name.render(self._stage_name, True, (200, 200, 220))
        name_surf.set_alpha(alpha)
        
        # Center text
        stage_x = (self._width - stage_surf.get_width()) // 2 + slide_x
        stage_y = banner_y + 30
        
        name_x = (self._width - name_surf.get_width()) // 2 + slide_x
        name_y = banner_y + 90
        
        self._screen.blit(stage_surf, (stage_x, stage_y))
        self._screen.blit(name_surf, (name_x, name_y))
    
    def _ease_out_expo(self, t: float) -> float:
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    def _ease_in_expo(self, t: float) -> float:
        return 0 if t == 0 else pow(2, 10 * t - 10)
    
    @property
    def is_active(self) -> bool:
        return self._active


class ConfirmDialog:
    """
    Confirmation dialog popup.
    """
    
    def __init__(self, screen: pygame.Surface):
        """Initialize dialog."""
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 42)
        self._font_message = pygame.font.Font(None, 28)
        self._font_button = pygame.font.Font(None, 32)
        
        self._active = False
        self._title = ""
        self._message = ""
        self._selected = 0  # 0 = Yes, 1 = No
        
        self._on_confirm: Optional[Callable] = None
        self._on_cancel: Optional[Callable] = None
        self._play_sound: Optional[Callable[[str], None]] = None
        
        # Button rects
        self._yes_rect = pygame.Rect(0, 0, 0, 0)
        self._no_rect = pygame.Rect(0, 0, 0, 0)
        
        # Animation
        self._anim_progress = 0.0
    
    def set_sound_callback(self, callback: Callable[[str], None]) -> None:
        self._play_sound = callback
    
    def show(
        self,
        title: str,
        message: str,
        on_confirm: Callable,
        on_cancel: Callable
    ) -> None:
        """Show confirmation dialog."""
        self._active = True
        self._title = title
        self._message = message
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._selected = 1  # Default to No
        self._anim_progress = 0.0
    
    def hide(self) -> None:
        """Hide dialog."""
        self._active = False
    
    def update(self, dt: float) -> None:
        """Update animation."""
        if self._active and self._anim_progress < 1.0:
            self._anim_progress = min(1.0, self._anim_progress + dt * 5)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self._active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                self._selected = 1 - self._selected
                if self._play_sound:
                    self._play_sound("menu_move")
                return True
            
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self._selected == 0:
                    if self._on_confirm:
                        self._on_confirm()
                else:
                    if self._on_cancel:
                        self._on_cancel()
                self._active = False
                if self._play_sound:
                    self._play_sound("menu_select")
                return True
            
            elif event.key == pygame.K_ESCAPE:
                if self._on_cancel:
                    self._on_cancel()
                self._active = False
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self._yes_rect.collidepoint(pos):
                if self._selected != 0:
                    self._selected = 0
                    if self._play_sound:
                        self._play_sound("menu_move")
            elif self._no_rect.collidepoint(pos):
                if self._selected != 1:
                    self._selected = 1
                    if self._play_sound:
                        self._play_sound("menu_move")
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                if self._yes_rect.collidepoint(pos):
                    if self._on_confirm:
                        self._on_confirm()
                    self._active = False
                    if self._play_sound:
                        self._play_sound("menu_select")
                    return True
                elif self._no_rect.collidepoint(pos):
                    if self._on_cancel:
                        self._on_cancel()
                    self._active = False
                    if self._play_sound:
                        self._play_sound("menu_select")
                    return True
        
        return False
    
    def draw(self) -> None:
        """Draw dialog."""
        if not self._active:
            return
        
        # Darken background
        overlay = pygame.Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * self._anim_progress)))
        self._screen.blit(overlay, (0, 0))
        
        # Dialog box
        box_width = 400
        box_height = 200
        box_x = (self._width - box_width) // 2
        box_y = (self._height - box_height) // 2
        
        # Scale in animation
        scale = 0.8 + 0.2 * self._anim_progress
        scaled_w = int(box_width * scale)
        scaled_h = int(box_height * scale)
        box_x = (self._width - scaled_w) // 2
        box_y = (self._height - scaled_h) // 2
        
        # Draw box
        box_surf = pygame.Surface((scaled_w, scaled_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (30, 30, 50, 240), box_surf.get_rect(), border_radius=15)
        pygame.draw.rect(box_surf, (80, 100, 150), box_surf.get_rect(), 3, border_radius=15)
        
        self._screen.blit(box_surf, (box_x, box_y))
        
        alpha = int(255 * self._anim_progress)
        
        # Title
        title_surf = self._font_title.render(self._title, True, (255, 200, 100))
        title_surf.set_alpha(alpha)
        title_x = box_x + (scaled_w - title_surf.get_width()) // 2
        self._screen.blit(title_surf, (title_x, box_y + 25))
        
        # Message
        msg_surf = self._font_message.render(self._message, True, (200, 200, 220))
        msg_surf.set_alpha(alpha)
        msg_x = box_x + (scaled_w - msg_surf.get_width()) // 2
        self._screen.blit(msg_surf, (msg_x, box_y + 75))
        
        # Buttons
        btn_width = 100
        btn_height = 40
        btn_y = box_y + scaled_h - 60
        
        yes_x = box_x + scaled_w // 2 - btn_width - 20
        no_x = box_x + scaled_w // 2 + 20
        
        self._yes_rect = pygame.Rect(yes_x, btn_y, btn_width, btn_height)
        self._no_rect = pygame.Rect(no_x, btn_y, btn_width, btn_height)
        
        # Draw Yes button
        yes_color = (80, 180, 100) if self._selected == 0 else (50, 60, 80)
        pygame.draw.rect(self._screen, yes_color, self._yes_rect, border_radius=8)
        if self._selected == 0:
            pygame.draw.rect(self._screen, (120, 220, 140), self._yes_rect, 2, border_radius=8)
        
        yes_text = self._font_button.render("Yes", True, (255, 255, 255))
        yes_text.set_alpha(alpha)
        self._screen.blit(
            yes_text,
            (yes_x + (btn_width - yes_text.get_width()) // 2,
             btn_y + (btn_height - yes_text.get_height()) // 2)
        )
        
        # Draw No button
        no_color = (180, 80, 80) if self._selected == 1 else (50, 60, 80)
        pygame.draw.rect(self._screen, no_color, self._no_rect, border_radius=8)
        if self._selected == 1:
            pygame.draw.rect(self._screen, (220, 120, 120), self._no_rect, 2, border_radius=8)
        
        no_text = self._font_button.render("No", True, (255, 255, 255))
        no_text.set_alpha(alpha)
        self._screen.blit(
            no_text,
            (no_x + (btn_width - no_text.get_width()) // 2,
             btn_y + (btn_height - no_text.get_height()) // 2)
        )
    
    @property
    def is_active(self) -> bool:
        return self._active
