"""
Graphic novel-style story presentation system.

Features:
- Character portraits with emotion expressions
- Typing text animation in character-specific dialog boxes
- Visual novel style presentation with enhanced visuals
"""

import math
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


# Typing animation speed (characters per second)
DEFAULT_TYPING_SPEED = 35


@dataclass
class DialogueMessage:
    """A single dialogue message."""
    character_id: str
    text: str
    emotion: str = "neutral"  # neutral, happy, sad, angry, surprised, worried, determined


# Character definitions with colors and styles
CHARACTER_STYLES = {
    "alex": {
        "name": "Alex",
        "box_color": (60, 120, 180),  # Blue
        "name_color": (150, 200, 255),
        "text_color": (255, 255, 255),
        "border_color": (100, 160, 220),
        "portrait_placeholder": "A",  # First letter for placeholder
    },
    "elena": {
        "name": "Dr. Elena Vex",
        "box_color": (120, 80, 140),  # Purple
        "name_color": (200, 160, 220),
        "text_color": (255, 255, 255),
        "border_color": (160, 120, 180),
        "portrait_placeholder": "E",
    },
    "kai": {
        "name": "Kai",
        "box_color": (140, 100, 60),  # Orange/brown
        "name_color": (255, 200, 150),
        "text_color": (255, 255, 255),
        "border_color": (180, 140, 100),
        "portrait_placeholder": "K",
    },
    "overseer": {
        "name": "The Overseer",
        "box_color": (80, 30, 50),  # Dark red
        "name_color": (255, 100, 120),
        "text_color": (230, 200, 200),
        "border_color": (150, 50, 70),
        "portrait_placeholder": "?",
    },
    "narrator": {
        "name": "",
        "box_color": (40, 40, 50),  # Dark gray
        "name_color": (180, 180, 200),
        "text_color": (220, 220, 230),
        "border_color": (80, 80, 100),
        "portrait_placeholder": "",
    },
}

# Emotion modifiers (slight color tints for different emotions)
EMOTION_TINTS = {
    "neutral": (0, 0, 0),
    "happy": (20, 30, 0),
    "sad": (-20, -10, 20),
    "angry": (40, -20, -20),
    "surprised": (10, 20, 30),
    "worried": (-10, -5, 15),
    "determined": (10, 10, -10),
    "confused": (5, -5, 25),
    "scared": (-15, -20, 10),
    "pleased": (15, 25, 5),
    "calm": (-5, 10, 20),
    "urgent": (30, -10, -5),
    "serious": (-5, -5, 5),
    "menacing": (30, -30, -20),
    "threatening": (40, -30, -25),
    "amazed": (20, 30, 40),
    "informative": (0, 10, 20),
    "encouraging": (10, 20, 10),
    "proud": (20, 15, 5),
    "relieved": (5, 20, 15),
    "wary": (-5, 0, 10),
    "challenging": (25, -5, -10),
    "impressed": (10, 15, 25),
    "terrified": (-20, -25, 15),
    "alarmed": (25, -15, -5),
    "shaken": (-10, -15, 10),
    "grave": (-15, -10, 5),
    "welcoming": (15, 20, 10),
    "smug": (20, 5, -10),
}


class StoryPresentation:
    """
    Graphic novel-style story presentation system.
    
    Displays dialogue with character-specific visual styles,
    typing animation, and portrait expressions.
    """
    
    def __init__(self, screen: pygame.Surface):
        """Initialize story presentation."""
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        pygame.font.init()
        
        # Fonts for dialogue - use a more stylized feel
        self._font_name = pygame.font.Font(None, 32)
        self._font_text = pygame.font.Font(None, 28)
        self._font_hint = pygame.font.Font(None, 20)
        
        # Current dialogue state
        self._current_message: Optional[DialogueMessage] = None
        self._displayed_chars = 0
        self._typing_speed = DEFAULT_TYPING_SPEED
        self._typing_timer = 0.0
        self._typing_complete = False
        
        # Dialogue queue
        self._dialogue_queue: List[DialogueMessage] = []
        self._dialogue_index = 0
        
        # Animation state
        self._time = 0.0
        self._box_anim_progress = 0.0
        self._portrait_anim_progress = 0.0
        
        # Callbacks
        self._on_dialogue_complete: Optional[Callable] = None
        self._on_all_complete: Optional[Callable] = None
        self._play_sound: Optional[Callable[[str], None]] = None
        
        # Active state
        self._active = False
        
        # Portrait cache
        self._portrait_cache: Dict[str, Dict[str, pygame.Surface]] = {}
        
        # Dialog box dimensions - positioned at bottom
        self._box_height = 160
        self._box_margin = 40
        self._portrait_size = 120
    
    def set_sound_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for playing sounds."""
        self._play_sound = callback
    
    def _play(self, sound: str) -> None:
        """Play a sound if callback is set."""
        if self._play_sound:
            self._play_sound(sound)
    
    def start_dialogue(self, messages: List[DialogueMessage],
                       on_complete: Optional[Callable] = None) -> None:
        """
        Start a dialogue sequence.
        
        Args:
            messages: List of dialogue messages to display
            on_complete: Callback when all dialogue is complete
        """
        self._dialogue_queue = messages
        self._dialogue_index = 0
        self._on_all_complete = on_complete
        self._active = True
        
        if messages:
            self._show_message(messages[0])
    
    def _show_message(self, message: DialogueMessage) -> None:
        """Show a new dialogue message."""
        self._current_message = message
        self._displayed_chars = 0
        self._typing_timer = 0.0
        self._typing_complete = False
        self._box_anim_progress = 0.0
        self._portrait_anim_progress = 0.0
        self._play("dialogue_show")
    
    def advance(self) -> bool:
        """
        Advance the dialogue.
        
        Returns True if there are more messages, False if complete.
        """
        if not self._current_message:
            return False
        
        if not self._typing_complete:
            # Skip to end of current message
            self._displayed_chars = len(self._current_message.text)
            self._typing_complete = True
            return True
        
        # Move to next message
        self._dialogue_index += 1
        
        if self._dialogue_index < len(self._dialogue_queue):
            self._show_message(self._dialogue_queue[self._dialogue_index])
            return True
        else:
            # All dialogue complete
            self._active = False
            if self._on_all_complete:
                self._on_all_complete()
            return False
    
    def skip_all(self) -> None:
        """Skip all remaining dialogue."""
        self._active = False
        if self._on_all_complete:
            self._on_all_complete()
    
    def update(self, dt: float) -> None:
        """Update dialogue animations."""
        if not self._active or not self._current_message:
            return
        
        self._time += dt
        
        # Animate dialog box appearing
        self._box_anim_progress = min(1.0, self._box_anim_progress + dt * 8)
        self._portrait_anim_progress = min(1.0, self._portrait_anim_progress + dt * 6)
        
        # Typing animation
        if not self._typing_complete:
            self._typing_timer += dt
            chars_to_show = int(self._typing_timer * self._typing_speed)
            
            if chars_to_show > self._displayed_chars:
                old_chars = self._displayed_chars
                self._displayed_chars = min(chars_to_show, len(self._current_message.text))
                
                # Play typing sound occasionally
                if (self._displayed_chars - old_chars) > 0:
                    self._play("text_type")
                
                if self._displayed_chars >= len(self._current_message.text):
                    self._typing_complete = True
    
    def draw(self) -> None:
        """Draw the story presentation overlay."""
        if not self._active or not self._current_message:
            return
        
        msg = self._current_message
        char_id = msg.character_id
        emotion = msg.emotion
        
        # Get character style
        style = CHARACTER_STYLES.get(char_id, CHARACTER_STYLES["narrator"])
        
        # Calculate positions with animation
        box_y = self._height - self._box_margin - self._box_height
        box_y += int(50 * (1.0 - self._ease_out_quad(self._box_anim_progress)))
        
        # Draw darkening overlay at top
        overlay = pygame.Surface((self._width, box_y), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 60))
        self._screen.blit(overlay, (0, 0))
        
        # Draw main dialog box
        self._draw_dialog_box(box_y, style, emotion)
        
        # Draw character portrait
        if char_id != "narrator":
            self._draw_portrait(box_y, style, emotion)
        
        # Draw name
        if style["name"]:
            self._draw_name(box_y, style)
        
        # Draw dialogue text with typing effect
        self._draw_dialogue_text(box_y, style)
        
        # Draw continue indicator
        if self._typing_complete:
            self._draw_continue_indicator()
    
    def _ease_out_quad(self, t: float) -> float:
        """Quadratic ease-out function."""
        return 1 - (1 - t) * (1 - t)
    
    def _draw_dialog_box(self, box_y: int, style: Dict, emotion: str) -> None:
        """Draw the character-specific dialog box."""
        box_x = self._box_margin + self._portrait_size + 20
        box_width = self._width - box_x - self._box_margin
        
        # Apply emotion tint to box color
        tint = EMOTION_TINTS.get(emotion, (0, 0, 0))
        box_color = tuple(max(0, min(255, c + t)) for c, t in zip(style["box_color"], tint))
        
        # Alpha based on animation
        alpha = int(220 * self._box_anim_progress)
        
        # Draw box with shadow
        shadow_rect = pygame.Rect(box_x + 5, box_y + 5, box_width, self._box_height)
        shadow = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, alpha // 2), shadow.get_rect(), border_radius=15)
        self._screen.blit(shadow, shadow_rect.topleft)
        
        # Main box
        box_rect = pygame.Rect(box_x, box_y, box_width, self._box_height)
        box = pygame.Surface((box_width, self._box_height), pygame.SRCALPHA)
        pygame.draw.rect(box, (*box_color, alpha), box.get_rect(), border_radius=15)
        
        # Border
        border_color = style["border_color"]
        pygame.draw.rect(box, (*border_color, alpha), box.get_rect(), 3, border_radius=15)
        
        self._screen.blit(box, box_rect.topleft)
        
        # Inner glow effect
        glow_rect = pygame.Rect(box_x + 5, box_y + 5, box_width - 10, self._box_height - 10)
        glow = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*border_color, 30), glow.get_rect(), border_radius=12)
        self._screen.blit(glow, glow_rect.topleft)
    
    def _draw_portrait(self, box_y: int, style: Dict, emotion: str) -> None:
        """Draw character portrait with emotion expression."""
        port_x = self._box_margin
        port_y = box_y + (self._box_height - self._portrait_size) // 2
        
        # Animation offset
        offset = int(20 * (1.0 - self._ease_out_quad(self._portrait_anim_progress)))
        port_x -= offset
        
        alpha = int(255 * self._portrait_anim_progress)
        
        # Portrait frame (rounded square)
        frame_rect = pygame.Rect(port_x, port_y, self._portrait_size, self._portrait_size)
        
        # Shadow
        shadow = pygame.Surface((self._portrait_size + 10, self._portrait_size + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, alpha // 3), shadow.get_rect(), border_radius=20)
        self._screen.blit(shadow, (port_x - 2, port_y + 5))
        
        # Portrait background
        port_bg = pygame.Surface((self._portrait_size, self._portrait_size), pygame.SRCALPHA)
        pygame.draw.rect(port_bg, (*style["box_color"], alpha), port_bg.get_rect(), border_radius=15)
        self._screen.blit(port_bg, frame_rect.topleft)
        
        # Portrait placeholder (character initial with emotion-based styling)
        tint = EMOTION_TINTS.get(emotion, (0, 0, 0))
        text_color = tuple(max(0, min(255, c + t * 2)) for c, t in zip(style["name_color"], tint))
        
        placeholder = style["portrait_placeholder"]
        if placeholder:
            font_large = pygame.font.Font(None, 80)
            char_surf = font_large.render(placeholder, True, text_color)
            char_surf.set_alpha(alpha)
            char_x = port_x + (self._portrait_size - char_surf.get_width()) // 2
            char_y = port_y + (self._portrait_size - char_surf.get_height()) // 2
            self._screen.blit(char_surf, (char_x, char_y))
        
        # Emotion indicator (small text below portrait)
        emotion_font = pygame.font.Font(None, 18)
        emotion_text = f"[{emotion}]"
        emotion_surf = emotion_font.render(emotion_text, True, (180, 180, 200))
        emotion_surf.set_alpha(alpha)
        emotion_x = port_x + (self._portrait_size - emotion_surf.get_width()) // 2
        emotion_y = port_y + self._portrait_size + 5
        self._screen.blit(emotion_surf, (emotion_x, emotion_y))
        
        # Portrait border
        border_surf = pygame.Surface((self._portrait_size + 6, self._portrait_size + 6), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (*style["border_color"], alpha), border_surf.get_rect(), 3, border_radius=15)
        self._screen.blit(border_surf, (port_x - 3, port_y - 3))
    
    def _draw_name(self, box_y: int, style: Dict) -> None:
        """Draw character name above dialog box."""
        box_x = self._box_margin + self._portrait_size + 20
        
        name_surf = self._font_name.render(style["name"], True, style["name_color"])
        name_y = box_y - 35
        
        # Name background
        name_bg_rect = pygame.Rect(box_x - 5, name_y - 5, name_surf.get_width() + 20, name_surf.get_height() + 10)
        name_bg = pygame.Surface((name_bg_rect.width, name_bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(name_bg, (*style["box_color"], 200), name_bg.get_rect(), border_radius=8)
        pygame.draw.rect(name_bg, (*style["border_color"], 200), name_bg.get_rect(), 2, border_radius=8)
        self._screen.blit(name_bg, name_bg_rect.topleft)
        
        self._screen.blit(name_surf, (box_x + 5, name_y))
    
    def _draw_dialogue_text(self, box_y: int, style: Dict) -> None:
        """Draw dialogue text with typing effect."""
        if not self._current_message:
            return
        
        box_x = self._box_margin + self._portrait_size + 40
        text_y = box_y + 25
        max_width = self._width - box_x - self._box_margin - 30
        
        # Get visible portion of text
        full_text = self._current_message.text
        visible_text = full_text[:self._displayed_chars]
        
        # Word wrap and draw
        words = visible_text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            test_surf = self._font_text.render(test_line, True, style["text_color"])
            
            if test_surf.get_width() > max_width and current_line:
                lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line.strip())
        
        # Draw lines
        for i, line in enumerate(lines[:4]):  # Max 4 lines
            line_surf = self._font_text.render(line, True, style["text_color"])
            self._screen.blit(line_surf, (box_x, text_y + i * 30))
    
    def _draw_continue_indicator(self) -> None:
        """Draw the continue/advance indicator."""
        indicator_x = self._width - self._box_margin - 60
        indicator_y = self._height - self._box_margin - 30
        
        # Pulsing animation
        pulse = 0.7 + 0.3 * math.sin(self._time * 4)
        alpha = int(200 * pulse)
        
        # Draw arrow or text
        font = pygame.font.Font(None, 24)
        text = "▼ Click to continue"
        text_surf = font.render(text, True, (200, 200, 220, alpha))
        self._screen.blit(text_surf, (indicator_x - text_surf.get_width(), indicator_y))
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self._active:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.advance()
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.advance()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.skip_all()
                return True
        
        return False
    
    @property
    def is_active(self) -> bool:
        return self._active
    
    @property
    def is_typing(self) -> bool:
        return self._active and not self._typing_complete
