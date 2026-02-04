"""
Story mode manager - placeholder for future implementation.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto


class StoryState(Enum):
    """Story mode states."""
    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    CHAPTER_COMPLETE = auto()
    STORY_COMPLETE = auto()


@dataclass
class StoryChapter:
    """
    Represents a single chapter in story mode.
    
    Each chapter has unique challenges and narrative.
    """
    id: int
    title: str
    description: str
    
    # Gameplay modifiers
    target_score: int = 1000
    target_lines: int = 10
    time_limit: Optional[float] = None  # In seconds, None = no limit
    
    # Special rules
    special_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Narrative
    intro_text: str = ""
    outro_text: str = ""
    
    # Unlocks
    unlocks: List[str] = field(default_factory=list)
    
    # State
    completed: bool = False
    best_score: int = 0
    best_time: float = 0.0


# Placeholder chapters - to be expanded
STORY_CHAPTERS = [
    StoryChapter(
        id=1,
        title="The Beginning",
        description="Learn the basics of Tetris.",
        target_score=500,
        target_lines=5,
        intro_text="Welcome to the world of Tetris. Your journey begins here...",
        outro_text="You've taken your first steps. The path ahead awaits."
    ),
    StoryChapter(
        id=2,
        title="Speed Challenge",
        description="Clear lines before time runs out!",
        target_score=1000,
        target_lines=10,
        time_limit=120.0,
        intro_text="Time is of the essence. Show your speed!",
        outro_text="You've proven your quickness. But greater challenges await."
    ),
    StoryChapter(
        id=3,
        title="The Tower",
        description="Build high without topping out.",
        target_score=2000,
        target_lines=20,
        special_rules={"garbage_lines": 5},
        intro_text="A tower of blocks awaits. Can you manage the chaos?",
        outro_text="The tower crumbles. Victory is yours."
    ),
    # More chapters to be added...
]


class StoryManager:
    """
    Manages story mode progression.
    
    This is a placeholder implementation that provides the basic structure
    for story mode. Full implementation to come later.
    """
    
    def __init__(self, save_dir: str = "saves"):
        """Initialize story manager."""
        self._save_dir = save_dir
        self._chapters: List[StoryChapter] = list(STORY_CHAPTERS)
        self._current_chapter: Optional[StoryChapter] = None
        self._state = StoryState.NOT_STARTED
        self._total_progress = 0.0
    
    def get_available_chapters(self) -> List[StoryChapter]:
        """Get list of available (unlocked) chapters."""
        available = []
        for i, chapter in enumerate(self._chapters):
            if i == 0 or (i > 0 and self._chapters[i - 1].completed):
                available.append(chapter)
        return available
    
    def start_chapter(self, chapter_id: int) -> Optional[StoryChapter]:
        """Start a chapter."""
        for chapter in self._chapters:
            if chapter.id == chapter_id:
                self._current_chapter = chapter
                self._state = StoryState.IN_PROGRESS
                return chapter
        return None
    
    def complete_chapter(self, score: int, time_played: float) -> bool:
        """
        Mark current chapter as complete.
        
        Returns True if this is a new completion.
        """
        if not self._current_chapter:
            return False
        
        was_completed = self._current_chapter.completed
        self._current_chapter.completed = True
        
        if score > self._current_chapter.best_score:
            self._current_chapter.best_score = score
        
        if self._current_chapter.best_time == 0 or time_played < self._current_chapter.best_time:
            self._current_chapter.best_time = time_played
        
        self._state = StoryState.CHAPTER_COMPLETE
        self._update_progress()
        
        return not was_completed
    
    def _update_progress(self) -> None:
        """Update total progress percentage."""
        completed = sum(1 for c in self._chapters if c.completed)
        self._total_progress = completed / len(self._chapters) if self._chapters else 0.0
        
        if completed == len(self._chapters):
            self._state = StoryState.STORY_COMPLETE
    
    def get_chapter_by_id(self, chapter_id: int) -> Optional[StoryChapter]:
        """Get a chapter by ID."""
        for chapter in self._chapters:
            if chapter.id == chapter_id:
                return chapter
        return None
    
    def reset(self) -> None:
        """Reset all story progress."""
        for chapter in self._chapters:
            chapter.completed = False
            chapter.best_score = 0
            chapter.best_time = 0.0
        
        self._current_chapter = None
        self._state = StoryState.NOT_STARTED
        self._total_progress = 0.0
    
    @property
    def current_chapter(self) -> Optional[StoryChapter]:
        return self._current_chapter
    
    @property
    def state(self) -> StoryState:
        return self._state
    
    @property
    def progress(self) -> float:
        """Get overall progress (0.0 to 1.0)."""
        return self._total_progress
    
    @property
    def chapters_completed(self) -> int:
        return sum(1 for c in self._chapters if c.completed)
    
    @property
    def total_chapters(self) -> int:
        return len(self._chapters)
