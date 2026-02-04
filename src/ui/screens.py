"""
Name entry and profile screens.
"""

import os
from typing import Optional, Callable

try:
    import pygame
except ImportError:
    import pygame_ce as pygame


class NameEntryScreen:
    """
    Screen for entering player name and optionally selecting avatar.
    """
    
    MAX_NAME_LENGTH = 12
    
    def __init__(self, screen: pygame.Surface):
        """Initialize name entry screen."""
        self._screen = screen
        self._width = screen.get_width()
        self._height = screen.get_height()
        
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 56)
        self._font_input = pygame.font.Font(None, 48)
        self._font_hint = pygame.font.Font(None, 28)
        self._font_button = pygame.font.Font(None, 36)
        
        self._active = False
        self._name = ""
        self._cursor_blink = 0.0
        self._avatar_path: Optional[str] = None
        self._avatar_surface: Optional[pygame.Surface] = None
        
        self._on_confirm: Optional[Callable[[str, Optional[str]], None]] = None
        self._on_cancel: Optional[Callable] = None
        self._play_sound: Optional[Callable[[str], None]] = None
        
        # UI state
        self._selected_button = 0  # 0=confirm, 1=avatar, 2=cancel
        
        # Button rects
        self._confirm_rect = pygame.Rect(0, 0, 0, 0)
        self._avatar_rect = pygame.Rect(0, 0, 0, 0)
        self._cancel_rect = pygame.Rect(0, 0, 0, 0)
    
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
    
    def hide(self) -> None:
        """Hide screen."""
        self._active = False
    
    def update(self, dt: float) -> None:
        """Update animations."""
        self._cursor_blink += dt
        if self._cursor_blink > 1.0:
            self._cursor_blink -= 1.0
    
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
                    if self._on_confirm:
                        self._on_confirm(self._name.strip(), self._avatar_path)
                    self._active = False
                    if self._play_sound:
                        self._play_sound("menu_select")
                return True
            
            elif event.key == pygame.K_BACKSPACE:
                if len(self._name) > 0:
                    self._name = self._name[:-1]
                return True
            
            elif event.key == pygame.K_TAB:
                self._selected_button = (self._selected_button + 1) % 3
                if self._play_sound:
                    self._play_sound("menu_move")
                return True
            
            elif event.unicode and len(event.unicode) == 1:
                if len(self._name) < self.MAX_NAME_LENGTH:
                    if event.unicode.isalnum() or event.unicode in " _-":
                        self._name += event.unicode
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                if self._confirm_rect.collidepoint(pos):
                    if len(self._name.strip()) > 0:
                        if self._on_confirm:
                            self._on_confirm(self._name.strip(), self._avatar_path)
                        self._active = False
                        if self._play_sound:
                            self._play_sound("menu_select")
                    return True
                elif self._avatar_rect.collidepoint(pos):
                    self._open_file_dialog()
                    return True
                elif self._cancel_rect.collidepoint(pos):
                    if self._on_cancel:
                        self._on_cancel()
                    self._active = False
                    return True
        
        elif event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self._confirm_rect.collidepoint(pos):
                self._selected_button = 0
            elif self._avatar_rect.collidepoint(pos):
                self._selected_button = 1
            elif self._cancel_rect.collidepoint(pos):
                self._selected_button = 2
        
        return False
    
    def _open_file_dialog(self) -> None:
        """Open file dialog for avatar selection."""
        # Note: This is a simplified version. In a full implementation,
        # you might use tkinter.filedialog or a custom file browser
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            
            file_path = filedialog.askopenfilename(
                title="Select Avatar Image",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("All files", "*.*")
                ]
            )
            
            root.destroy()
            
            if file_path:
                self._load_avatar(file_path)
        except Exception:
            # Fallback if tkinter not available
            pass
    
    def _load_avatar(self, path: str) -> bool:
        """Load avatar from file."""
        try:
            img = pygame.image.load(path)
            # Scale to 64x64
            self._avatar_surface = pygame.transform.smoothscale(img, (64, 64))
            self._avatar_path = path
            return True
        except Exception:
            return False
    
    def draw(self) -> None:
        """Draw name entry screen."""
        if not self._active:
            return
        
        # Background
        self._screen.fill((15, 15, 25))
        
        # Title
        title = self._font_title.render("Enter Your Name", True, (100, 200, 255))
        title_x = (self._width - title.get_width()) // 2
        self._screen.blit(title, (title_x, 100))
        
        # Name input box
        input_width = 400
        input_height = 60
        input_x = (self._width - input_width) // 2
        input_y = 200
        
        input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
        pygame.draw.rect(self._screen, (30, 30, 50), input_rect, border_radius=10)
        pygame.draw.rect(self._screen, (80, 120, 180), input_rect, 3, border_radius=10)
        
        # Name text with cursor
        display_name = self._name
        if self._cursor_blink < 0.5:
            display_name += "|"
        
        name_surf = self._font_input.render(display_name, True, (255, 255, 255))
        name_x = input_x + 20
        name_y = input_y + (input_height - name_surf.get_height()) // 2
        self._screen.blit(name_surf, (name_x, name_y))
        
        # Hint
        hint = self._font_hint.render(
            f"Max {self.MAX_NAME_LENGTH} characters. Press ENTER to confirm.",
            True, (120, 120, 140)
        )
        hint_x = (self._width - hint.get_width()) // 2
        self._screen.blit(hint, (hint_x, input_y + input_height + 15))
        
        # Avatar section
        avatar_section_y = 320
        avatar_label = self._font_hint.render("Profile Picture (optional)", True, (150, 150, 170))
        self._screen.blit(avatar_label, ((self._width - avatar_label.get_width()) // 2, avatar_section_y))
        
        # Avatar display/button
        avatar_box_size = 80
        avatar_box_x = (self._width - avatar_box_size) // 2
        avatar_box_y = avatar_section_y + 35
        
        self._avatar_rect = pygame.Rect(avatar_box_x, avatar_box_y, avatar_box_size, avatar_box_size)
        
        if self._avatar_surface:
            # Draw avatar
            self._screen.blit(
                pygame.transform.smoothscale(self._avatar_surface, (avatar_box_size, avatar_box_size)),
                (avatar_box_x, avatar_box_y)
            )
        else:
            pygame.draw.rect(self._screen, (40, 40, 60), self._avatar_rect, border_radius=10)
            plus = self._font_title.render("+", True, (100, 100, 120))
            self._screen.blit(
                plus,
                (avatar_box_x + (avatar_box_size - plus.get_width()) // 2,
                 avatar_box_y + (avatar_box_size - plus.get_height()) // 2)
            )
        
        if self._selected_button == 1:
            pygame.draw.rect(self._screen, (100, 180, 255), self._avatar_rect, 3, border_radius=10)
        else:
            pygame.draw.rect(self._screen, (60, 60, 80), self._avatar_rect, 2, border_radius=10)
        
        # Buttons
        btn_width = 150
        btn_height = 50
        btn_y = 480
        btn_spacing = 30
        
        total_width = btn_width * 2 + btn_spacing
        start_x = (self._width - total_width) // 2
        
        # Confirm button
        self._confirm_rect = pygame.Rect(start_x, btn_y, btn_width, btn_height)
        confirm_color = (60, 160, 100) if self._selected_button == 0 else (40, 80, 60)
        pygame.draw.rect(self._screen, confirm_color, self._confirm_rect, border_radius=10)
        if self._selected_button == 0:
            pygame.draw.rect(self._screen, (100, 220, 140), self._confirm_rect, 2, border_radius=10)
        
        confirm_text = self._font_button.render("START", True, (255, 255, 255))
        self._screen.blit(
            confirm_text,
            (self._confirm_rect.x + (btn_width - confirm_text.get_width()) // 2,
             self._confirm_rect.y + (btn_height - confirm_text.get_height()) // 2)
        )
        
        # Cancel button
        self._cancel_rect = pygame.Rect(start_x + btn_width + btn_spacing, btn_y, btn_width, btn_height)
        cancel_color = (160, 60, 60) if self._selected_button == 2 else (80, 40, 40)
        pygame.draw.rect(self._screen, cancel_color, self._cancel_rect, border_radius=10)
        if self._selected_button == 2:
            pygame.draw.rect(self._screen, (220, 100, 100), self._cancel_rect, 2, border_radius=10)
        
        cancel_text = self._font_button.render("BACK", True, (255, 255, 255))
        self._screen.blit(
            cancel_text,
            (self._cancel_rect.x + (btn_width - cancel_text.get_width()) // 2,
             self._cancel_rect.y + (btn_height - cancel_text.get_height()) // 2)
        )
    
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
