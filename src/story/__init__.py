"""
Story mode package - graphic novel-style story presentation.

The story mode includes:
- Multiple chapters with unique gameplay challenges
- Narrative elements between stages with typing text animations
- Character portraits with emotion expressions
- Character-specific dialog box styles
- Special game modes and modifiers
- Unlockable content and achievements
"""

from .story_manager import StoryManager, StoryChapter, StoryState, DialogueLine, CHARACTERS
from .story_presentation import StoryPresentation, DialogueMessage

__all__ = [
    'StoryManager', 'StoryChapter', 'StoryState', 'DialogueLine', 'CHARACTERS',
    'StoryPresentation', 'DialogueMessage'
]
