"""
Event State for narrative events, dialogue, and cutscenes.
"""

import pygame
from typing import Optional, List, Dict, Any
from .base_state import BaseState
from ..settings import get_settings


class EventState(BaseState):
    """
    State for narrative events and dialogue.
    
    Features:
    - Text-based dialogue
    - Branching choices
    - Character portraits (optional)
    - Event-driven state changes
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # Event data
        self.event_id: str = ""
        self.event_data: Dict[str, Any] = {}
        
        # Dialogue state
        self.dialogue_lines: List[Dict] = []
        self.current_line_index: int = 0
        self.choices: List[Dict] = []
        self.selected_choice: int = 0
        
        # Text display
        self.displayed_text: str = ""
        self.text_progress: float = 0.0
        self.text_speed: float = 30.0  # characters per second
        self.text_complete: bool = False
        
        # Fonts
        self._font: Optional[pygame.font.Font] = None
        self._name_font: Optional[pygame.font.Font] = None
    
    def startup(self, persistent: dict) -> None:
        """Initialize event state."""
        super().startup(persistent)
        
        pygame.font.init()
        self._font = pygame.font.Font(None, self.settings.FONT_SIZE_MEDIUM)
        self._name_font = pygame.font.Font(None, self.settings.FONT_SIZE_LARGE)
        
        # Get event data
        self.event_id = persistent.get('event_id', '')
        self.event_data = persistent.get('event_data', {})
        
        self.dialogue_lines = self.event_data.get('dialogue', [])
        self.current_line_index = 0
        self.choices = []
        self.selected_choice = 0
        
        self._start_line()
    
    def _start_line(self) -> None:
        """Start displaying a new dialogue line."""
        if self.current_line_index >= len(self.dialogue_lines):
            self._end_dialogue()
            return
        
        line = self.dialogue_lines[self.current_line_index]
        self.displayed_text = ""
        self.text_progress = 0.0
        self.text_complete = False
        
        # Check for choices on this line
        self.choices = line.get('choices', [])
        if self.choices:
            self.selected_choice = 0
    
    def _end_dialogue(self) -> None:
        """End the dialogue and return to game."""
        # Store any outcomes
        outcomes = self.event_data.get('outcomes', {})
        self.change_state('game', event_outcomes=outcomes)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle event input."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._advance()
            elif event.key == pygame.K_UP and self.choices:
                self.selected_choice = max(0, self.selected_choice - 1)
            elif event.key == pygame.K_DOWN and self.choices:
                self.selected_choice = min(len(self.choices) - 1, 
                                          self.selected_choice + 1)
            elif event.key == pygame.K_ESCAPE:
                # Skip to end
                self._end_dialogue()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._advance()
    
    def _advance(self) -> None:
        """Advance to next line or complete current line."""
        if not self.text_complete:
            # Complete current line instantly
            if self.current_line_index < len(self.dialogue_lines):
                line = self.dialogue_lines[self.current_line_index]
                self.displayed_text = line.get('text', '')
                self.text_complete = True
        elif self.choices:
            # Select choice and proceed
            self._select_choice(self.selected_choice)
        else:
            # Go to next line
            self.current_line_index += 1
            self._start_line()
    
    def _select_choice(self, choice_index: int) -> None:
        """Handle choice selection."""
        if choice_index >= len(self.choices):
            return
        
        choice = self.choices[choice_index]
        
        # Apply choice effects
        effects = choice.get('effects', {})
        if effects:
            current_outcomes = self.event_data.get('outcomes', {})
            current_outcomes.update(effects)
            self.event_data['outcomes'] = current_outcomes
        
        # Jump to next line or specific line
        next_line = choice.get('next_line', self.current_line_index + 1)
        self.current_line_index = next_line
        self.choices = []
        self._start_line()
    
    def update(self, dt: float) -> None:
        """Update text animation."""
        if self.current_line_index >= len(self.dialogue_lines):
            return
        
        if self.text_complete:
            return
        
        line = self.dialogue_lines[self.current_line_index]
        full_text = line.get('text', '')
        
        self.text_progress += self.text_speed * dt
        chars_to_show = int(self.text_progress)
        
        if chars_to_show >= len(full_text):
            self.displayed_text = full_text
            self.text_complete = True
        else:
            self.displayed_text = full_text[:chars_to_show]
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the event dialogue."""
        screen_w, screen_h = screen.get_size()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        # Dialogue box
        box_width = min(800, screen_w - 100)
        box_height = 200
        box_x = (screen_w - box_width) // 2
        box_y = screen_h - box_height - 50
        
        pygame.draw.rect(screen, self.settings.COLOR_UI_BG,
                        (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, self.settings.COLOR_UI_BORDER,
                        (box_x, box_y, box_width, box_height), 3)
        
        if self.current_line_index < len(self.dialogue_lines):
            line = self.dialogue_lines[self.current_line_index]
            
            # Speaker name
            speaker = line.get('speaker', '')
            if speaker and self._name_font:
                name_surface = self._name_font.render(speaker, True, 
                                                      self.settings.COLOR_TEXT_HIGHLIGHT)
                screen.blit(name_surface, (box_x + 20, box_y + 15))
            
            # Dialogue text
            if self._font:
                text_y = box_y + 50 if speaker else box_y + 20
                self._render_wrapped_text(screen, self.displayed_text,
                                         box_x + 20, text_y,
                                         box_width - 40, self._font)
        
        # Choices
        if self.choices and self.text_complete:
            self._render_choices(screen, box_x, box_y - 10 - len(self.choices) * 35)
        
        # Continue indicator
        if self.text_complete and not self.choices:
            if self._font:
                continue_text = "Press SPACE to continue..."
                continue_surface = self._font.render(continue_text, True, 
                                                     (100, 100, 120))
                continue_rect = continue_surface.get_rect(
                    bottomright=(box_x + box_width - 20, box_y + box_height - 10)
                )
                screen.blit(continue_surface, continue_rect)
    
    def _render_wrapped_text(self, screen: pygame.Surface, text: str,
                            x: int, y: int, max_width: int,
                            font: pygame.font.Font) -> None:
        """Render text with word wrapping."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        line_height = font.get_linesize()
        for i, line in enumerate(lines):
            line_surface = font.render(line, True, self.settings.COLOR_TEXT)
            screen.blit(line_surface, (x, y + i * line_height))
    
    def _render_choices(self, screen: pygame.Surface, x: int, y: int) -> None:
        """Render choice options."""
        if not self._font:
            return
        
        for i, choice in enumerate(self.choices):
            choice_y = y + i * 35
            
            # Selection indicator
            if i == self.selected_choice:
                indicator_color = self.settings.COLOR_TEXT_HIGHLIGHT
                pygame.draw.polygon(screen, indicator_color, [
                    (x + 10, choice_y + 10),
                    (x + 10, choice_y + 24),
                    (x + 22, choice_y + 17)
                ])
            
            # Choice text
            color = self.settings.COLOR_TEXT_HIGHLIGHT if i == self.selected_choice \
                    else self.settings.COLOR_TEXT
            choice_text = choice.get('text', '')
            choice_surface = self._font.render(choice_text, True, color)
            screen.blit(choice_surface, (x + 30, choice_y + 8))
