"""
Name entry and profile screens.
"""

import os
import math
from typing import Optional, Callable, List

try:
    import pygame
except ImportError:
    import pygame_ce as pygame

from settings import AVATAR_DIRECTORY, DEFAULT_AVATARS


class NameEntryScreen:
    """
    Screen for entering player name and selecting avatar.
    
    Features:
    - "Add Player" title
    - "Enter Your Name" animated placeholder
    - 10 avatar selection slots
    """
    
    MAX_NAME_LENGTH = 12
    
    def __init__(self, screen: pygame.Surface):
        """Initialize name entry screen."""
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 56)
        self._font_input = pygame.font.Font(None, 42)
        self._font_hint = pygame.font.Font(None, 24)
        self._font_button = pygame.font.Font(None, 32)
        self._font_label = pygame.font.Font(None, 20)
        
        self._active = False
        self._name = ""
        self._cursor_blink = 0.0
        self._input_focused = False  # For animated placeholder
        self._label_anim = 0.0  # Animation for floating label
        self._time = 0.0
        
        # Avatar selection
        self._selected_avatar_idx = -1  # -1 = no selection (default)
        self._avatar_surfaces: List[Optional[pygame.Surface]] = []
        self._avatar_rects: List[pygame.Rect] = []
        self._load_default_avatars()
        
        self._on_confirm: Optional[Callable[[str, Optional[str]], None]] = None
        self._on_cancel: Optional[Callable] = None
        self._play_sound: Optional[Callable[[str], None]] = None
        
        # UI state
        self._selected_button = 0  # 0=confirm, 1=cancel
        
        # Rects
        self._input_rect = pygame.Rect(0, 0, 0, 0)
        self._confirm_rect = pygame.Rect(0, 0, 0, 0)
        self._cancel_rect = pygame.Rect(0, 0, 0, 0)
    
    def _load_default_avatars(self) -> None:
        """Load default avatar images."""
        self._avatar_surfaces = []
        for avatar_name in DEFAULT_AVATARS:
            path = os.path.join(AVATAR_DIRECTORY, avatar_name)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    img = pygame.transform.smoothscale(img, (50, 50))
                    self._avatar_surfaces.append(img)
                except Exception:
                    self._avatar_surfaces.append(None)
            else:
                self._avatar_surfaces.append(None)
    
    def set_sound_callback(self, callback: Callable[[str], None]) -> None:
        self._play_sound = callback
    
    def show(
        self,
        on_confirm: Callable[[str, Optional[str]], None],
        on_cancel: Callable = None,
        initial_name: str = ""
    ) -> None:
        """Show name entry screen."""
        self._active = True
        self._name = initial_name
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._selected_button = 0
        self._cursor_blink = 0.0
        self._input_focused = len(initial_name) > 0
        self._label_anim = 1.0 if len(initial_name) > 0 else 0.0
        self._selected_avatar_idx = -1
    
    def hide(self) -> None:
        """Hide screen."""
        self._active = False
    
    def update(self, dt: float) -> None:
        """Update animations."""
        self._time += dt
        self._cursor_blink += dt
        if self._cursor_blink > 1.0:
            self._cursor_blink -= 1.0
        
        # Animate label floating up
        target = 1.0 if (self._input_focused or len(self._name) > 0) else 0.0
        self._label_anim += (target - self._label_anim) * min(1.0, dt * 10)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self._active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._on_cancel:
                    self._on_cancel()
                self._active = False
                return True
            
            elif event.key == pygame.K_RETURN:
                if len(self._name.strip()) > 0:
                    avatar_path = None
                    if 0 <= self._selected_avatar_idx < len(DEFAULT_AVATARS):
                        avatar_path = os.path.join(AVATAR_DIRECTORY, DEFAULT_AVATARS[self._selected_avatar_idx])
                    if self._on_confirm:
                        self._on_confirm(self._name.strip(), avatar_path)
                    self._active = False
                    if self._play_sound:
                        self._play_sound("menu_select")
                return True
            
            elif event.key == pygame.K_BACKSPACE:
                if len(self._name) > 0:
                    self._name = self._name[:-1]
                return True
            
            elif event.key == pygame.K_TAB:
                self._selected_button = (self._selected_button + 1) % 2
                if self._play_sound:
                    self._play_sound("menu_move")
                return True
            
            elif event.unicode and len(event.unicode) == 1:
                if len(self._name) < self.MAX_NAME_LENGTH:
                    if event.unicode.isalnum() or event.unicode in " _-":
                        self._name += event.unicode
                        self._input_focused = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                
                # Check input box click
                if self._input_rect.collidepoint(pos):
                    self._input_focused = True
                    return True
                
                # Check avatar clicks
                for i, rect in enumerate(self._avatar_rects):
                    if rect.collidepoint(pos):
                        # Toggle selection: click same avatar to deselect, click different to select
                        if self._selected_avatar_idx == i:
                            self._selected_avatar_idx = -1  # Deselect
                        else:
                            self._selected_avatar_idx = i  # Select new avatar
                        if self._play_sound:
                            self._play_sound("menu_move")
                        return True
                
                # Check button clicks
                if self._confirm_rect.collidepoint(pos):
                    if len(self._name.strip()) > 0:
                        avatar_path = None
                        if 0 <= self._selected_avatar_idx < len(DEFAULT_AVATARS):
                            avatar_path = os.path.join(AVATAR_DIRECTORY, DEFAULT_AVATARS[self._selected_avatar_idx])
                        if self._on_confirm:
                            self._on_confirm(self._name.strip(), avatar_path)
                        self._active = False
                        if self._play_sound:
                            self._play_sound("menu_select")
                    return True
                
                if self._cancel_rect.collidepoint(pos):
                    if self._on_cancel:
                        self._on_cancel()
                    self._active = False
                    return True
        
        elif event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self._confirm_rect.collidepoint(pos):
                self._selected_button = 0
            elif self._cancel_rect.collidepoint(pos):
                self._selected_button = 1
        
        return False
    
    def draw(self) -> None:
        """Draw name entry screen."""
        if not self._active:
            return
        
        # Background
        self._draw_background()
        
        # Title - "Add Player"
        title = self._font_title.render("Add Player", True, (100, 180, 255))
        title_x = (self._width - title.get_width()) // 2
        self._screen.blit(title, (title_x, 60))
        
        # Name input section
        self._draw_name_input()
        
        # Avatar selection section
        self._draw_avatar_selection()
        
        # Buttons
        self._draw_buttons()
    
    def _draw_background(self) -> None:
        """Draw gradient background."""
        for y in range(self._height):
            progress = y / self._height
            r = int(15 + progress * 10)
            g = int(15 + progress * 8)
            b = int(25 + progress * 15)
            pygame.draw.line(self._screen, (r, g, b), (0, y), (self._width, y))
        
        # Subtle grid
        for x in range(0, self._width, 50):
            for y in range(0, self._height, 50):
                s = pygame.Surface((48, 48), pygame.SRCALPHA)
                s.fill((35, 35, 50, 8))
                self._screen.blit(s, (x + 1, y + 1))
    
    def _draw_name_input(self) -> None:
        """Draw name input box with animated placeholder."""
        input_width = 400
        input_height = 55
        input_x = (self._width - input_width) // 2
        input_y = 160
        
        self._input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
        
        # Input box
        pygame.draw.rect(self._screen, (35, 32, 50), self._input_rect, border_radius=10)
        border_color = (100, 180, 255) if self._input_focused else (70, 65, 90)
        pygame.draw.rect(self._screen, border_color, self._input_rect, 2, border_radius=10)
        
        # Floating label / placeholder
        placeholder = "Enter Your Name"
        if self._label_anim > 0.01:
            # Floating label (above input)
            label_y = input_y - 12 - int(15 * self._label_anim)
            label_size = int(20 + 4 * (1 - self._label_anim))
            label_font = pygame.font.Font(None, label_size)
            label_color = (
                int(100 + 80 * self._label_anim),
                int(140 + 40 * self._label_anim),
                int(200 + 55 * self._label_anim)
            )
            label = label_font.render(placeholder, True, label_color)
            self._screen.blit(label, (input_x + 15, label_y))
        
        if self._label_anim < 0.99 and len(self._name) == 0:
            # Placeholder inside input
            alpha = int(180 * (1 - self._label_anim))
            placeholder_surf = self._font_input.render(placeholder, True, (100, 95, 120))
            placeholder_surf.set_alpha(alpha)
            self._screen.blit(placeholder_surf, (input_x + 15, input_y + 10))
        
        # Name text with cursor
        display_name = self._name
        if self._cursor_blink < 0.5:
            display_name += "|"
        
        name_surf = self._font_input.render(display_name, True, (255, 255, 255))
        self._screen.blit(name_surf, (input_x + 15, input_y + 10))
        
        # Character count
        count_text = f"{len(self._name)}/{self.MAX_NAME_LENGTH}"
        count_surf = self._font_label.render(count_text, True, (120, 115, 140))
        self._screen.blit(count_surf, (input_x + input_width - count_surf.get_width() - 10, input_y + input_height + 5))
    
    def _draw_avatar_selection(self) -> None:
        """Draw avatar selection grid."""
        section_y = 260
        
        # Section label
        label = self._font_hint.render("Choose an Avatar (optional)", True, (160, 155, 185))
        label_x = (self._width - label.get_width()) // 2
        self._screen.blit(label, (label_x, section_y))
        
        # Avatar grid - 10 slots in 2 rows of 5
        avatar_size = 55
        spacing = 15
        total_width = 5 * avatar_size + 4 * spacing
        start_x = (self._width - total_width) // 2
        start_y = section_y + 35
        
        self._avatar_rects = []
        
        for i in range(10):
            row = i // 5
            col = i % 5
            
            x = start_x + col * (avatar_size + spacing)
            y = start_y + row * (avatar_size + spacing)
            
            rect = pygame.Rect(x, y, avatar_size, avatar_size)
            self._avatar_rects.append(rect)
            
            # Background
            is_selected = self._selected_avatar_idx == i
            bg_color = (60, 55, 80) if is_selected else (40, 38, 55)
            pygame.draw.rect(self._screen, bg_color, rect, border_radius=10)
            
            # Avatar image or placeholder
            if i < len(self._avatar_surfaces) and self._avatar_surfaces[i]:
                # Draw avatar
                avatar = self._avatar_surfaces[i]
                self._screen.blit(avatar, (x + 2, y + 2))
            else:
                # Placeholder number
                num_font = pygame.font.Font(None, 28)
                num = num_font.render(str(i + 1), True, (90, 85, 110))
                num_x = x + (avatar_size - num.get_width()) // 2
                num_y = y + (avatar_size - num.get_height()) // 2
                self._screen.blit(num, (num_x, num_y))
            
            # Selection border
            if is_selected:
                pygame.draw.rect(self._screen, (100, 180, 255), rect, 3, border_radius=10)
            else:
                pygame.draw.rect(self._screen, (70, 65, 90), rect, 1, border_radius=10)
    
    def _draw_buttons(self) -> None:
        """Draw confirm and cancel buttons."""
        btn_width = 140
        btn_height = 48
        btn_y = 440
        btn_spacing = 30
        
        total_width = btn_width * 2 + btn_spacing
        start_x = (self._width - total_width) // 2
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Confirm button
        self._confirm_rect = pygame.Rect(start_x, btn_y, btn_width, btn_height)
        confirm_hovered = self._confirm_rect.collidepoint(mouse_pos) or self._selected_button == 0
        
        confirm_bg = (50, 100, 80) if confirm_hovered else (40, 70, 55)
        pygame.draw.rect(self._screen, confirm_bg, self._confirm_rect, border_radius=10)
        
        if confirm_hovered:
            pygame.draw.rect(self._screen, (100, 200, 150), self._confirm_rect, 2, border_radius=10)
        
        confirm_text = self._font_button.render("START", True, (255, 255, 255))
        text_x = self._confirm_rect.x + (btn_width - confirm_text.get_width()) // 2
        text_y = self._confirm_rect.y + (btn_height - confirm_text.get_height()) // 2
        self._screen.blit(confirm_text, (text_x, text_y))
        
        # Cancel button
        self._cancel_rect = pygame.Rect(start_x + btn_width + btn_spacing, btn_y, btn_width, btn_height)
        cancel_hovered = self._cancel_rect.collidepoint(mouse_pos) or self._selected_button == 1
        
        cancel_bg = (100, 50, 50) if cancel_hovered else (70, 40, 40)
        pygame.draw.rect(self._screen, cancel_bg, self._cancel_rect, border_radius=10)
        
        if cancel_hovered:
            pygame.draw.rect(self._screen, (200, 100, 100), self._cancel_rect, 2, border_radius=10)
        
        cancel_text = self._font_button.render("BACK", True, (255, 255, 255))
        text_x = self._cancel_rect.x + (btn_width - cancel_text.get_width()) // 2
        text_y = self._cancel_rect.y + (btn_height - cancel_text.get_height()) // 2
        self._screen.blit(cancel_text, (text_x, text_y))
    
    @property
    def is_active(self) -> bool:
        return self._active


class LeaderboardScreen:
    """
    Leaderboard display screen.
    """
    
    def __init__(self, screen: pygame.Surface):
        """Initialize leaderboard screen."""
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 56)
        self._font_header = pygame.font.Font(None, 28)
        self._font_entry = pygame.font.Font(None, 30)
        self._font_button = pygame.font.Font(None, 36)
        
        self._active = False
        self._entries = []
        self._scroll_offset = 0
        self._highlight_rank = -1  # Rank to highlight (1-indexed)
        
        self._on_close: Optional[Callable] = None
        self._play_sound: Optional[Callable[[str], None]] = None
        
        self._close_rect = pygame.Rect(0, 0, 0, 0)
    
    def set_sound_callback(self, callback: Callable[[str], None]) -> None:
        self._play_sound = callback
    
    def show(self, entries: list, on_close: Callable = None, highlight_rank: int = -1) -> None:
        """Show leaderboard."""
        self._active = True
        self._entries = entries
        self._on_close = on_close
        self._scroll_offset = 0
        self._highlight_rank = highlight_rank
    
    def hide(self) -> None:
        self._active = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self._active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                if self._on_close:
                    self._on_close()
                self._active = False
                if self._play_sound:
                    self._play_sound("menu_select")
                return True
            elif event.key == pygame.K_UP:
                self._scroll_offset = max(0, self._scroll_offset - 1)
                return True
            elif event.key == pygame.K_DOWN:
                max_scroll = max(0, len(self._entries) - 8)
                self._scroll_offset = min(max_scroll, self._scroll_offset + 1)
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._close_rect.collidepoint(event.pos):
                    if self._on_close:
                        self._on_close()
                    self._active = False
                    if self._play_sound:
                        self._play_sound("menu_select")
                    return True
            elif event.button == 4:  # Scroll up
                self._scroll_offset = max(0, self._scroll_offset - 1)
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self._entries) - 8)
                self._scroll_offset = min(max_scroll, self._scroll_offset + 1)
        
        return False
    
    def update(self, dt: float) -> None:
        pass
    
    def draw(self) -> None:
        """Draw leaderboard."""
        if not self._active:
            return
        
        # Background
        self._screen.fill((15, 15, 25))
        
        # Title
        title = self._font_title.render("LEADERBOARD", True, (255, 220, 100))
        title_x = (self._width - title.get_width()) // 2
        self._screen.blit(title, (title_x, 40))
        
        # Header
        header_y = 100
        headers = ["RANK", "NAME", "SCORE", "STAGE", "TIME"]
        header_x = [80, 170, 380, 520, 620]
        
        for i, (text, x) in enumerate(zip(headers, header_x)):
            surf = self._font_header.render(text, True, (100, 150, 200))
            self._screen.blit(surf, (x, header_y))
        
        # Divider
        pygame.draw.line(
            self._screen, (50, 60, 80),
            (60, header_y + 30), (self._width - 60, header_y + 30), 2
        )
        
        # Entries
        entry_start_y = 145
        entry_height = 45
        visible_entries = 8
        
        for i, entry in enumerate(self._entries[self._scroll_offset:self._scroll_offset + visible_entries]):
            rank = self._scroll_offset + i + 1
            y = entry_start_y + i * entry_height
            
            # Highlight background
            if rank == self._highlight_rank:
                highlight_rect = pygame.Rect(60, y - 5, self._width - 120, entry_height - 5)
                pygame.draw.rect(self._screen, (50, 80, 60), highlight_rect, border_radius=8)
            elif i % 2 == 0:
                row_rect = pygame.Rect(60, y - 5, self._width - 120, entry_height - 5)
                pygame.draw.rect(self._screen, (25, 25, 35), row_rect, border_radius=5)
            
            # Rank with medal colors
            rank_color = (255, 255, 255)
            if rank == 1:
                rank_color = (255, 215, 0)  # Gold
            elif rank == 2:
                rank_color = (192, 192, 192)  # Silver
            elif rank == 3:
                rank_color = (205, 127, 50)  # Bronze
            
            rank_text = self._font_entry.render(f"#{rank}", True, rank_color)
            self._screen.blit(rank_text, (header_x[0], y))
            
            name_text = self._font_entry.render(entry.player_name[:12], True, (220, 220, 230))
            self._screen.blit(name_text, (header_x[1], y))
            
            score_text = self._font_entry.render(f"{entry.score:,}", True, (255, 255, 255))
            self._screen.blit(score_text, (header_x[2], y))
            
            # Show stage with name if available
            stage_display = getattr(entry, 'stage_name', str(entry.stage))
            stage_text = self._font_entry.render(stage_display, True, (180, 220, 180))
            self._screen.blit(stage_text, (header_x[3], y))
            
            time_text = self._font_entry.render(entry.formatted_time, True, (180, 180, 220))
            self._screen.blit(time_text, (header_x[4], y))
        
        # Empty state
        if not self._entries:
            empty = self._font_entry.render("No scores yet. Be the first!", True, (100, 100, 120))
            self._screen.blit(empty, ((self._width - empty.get_width()) // 2, 250))
        
        # Scroll indicator
        if len(self._entries) > visible_entries:
            total = len(self._entries)
            bar_height = 200
            bar_y = entry_start_y
            thumb_height = max(30, int(bar_height * visible_entries / total))
            thumb_y = bar_y + int((bar_height - thumb_height) * self._scroll_offset / (total - visible_entries))
            
            pygame.draw.rect(self._screen, (40, 40, 50), (self._width - 40, bar_y, 8, bar_height), border_radius=4)
            pygame.draw.rect(self._screen, (80, 100, 130), (self._width - 40, thumb_y, 8, thumb_height), border_radius=4)
        
        # Close button
        btn_width = 150
        btn_height = 50
        btn_x = (self._width - btn_width) // 2
        btn_y = self._height - 80
        
        self._close_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self._screen, (60, 80, 120), self._close_rect, border_radius=10)
        pygame.draw.rect(self._screen, (100, 140, 200), self._close_rect, 2, border_radius=10)
        
        close_text = self._font_button.render("CLOSE", True, (255, 255, 255))
        self._screen.blit(
            close_text,
            (btn_x + (btn_width - close_text.get_width()) // 2,
             btn_y + (btn_height - close_text.get_height()) // 2)
        )
    
    @property
    def is_active(self) -> bool:
        return self._active
