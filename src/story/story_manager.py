"""
Story mode manager - expanded implementation with characters and plot.
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
class Character:
    """
    Represents a story character.
    """
    id: str
    name: str
    title: str = ""
    description: str = ""
    portrait: Optional[str] = None  # Path to portrait image
    
    def get_dialogue_name(self) -> str:
        """Get name for dialogue display."""
        if self.title:
            return f"{self.name} - {self.title}"
        return self.name


# Main characters
CHARACTERS = {
    "alex": Character(
        id="alex",
        name="Alex",
        title="The Shaper",
        description="A young architect student who discovers the power to manipulate geometric patterns."
    ),
    "elena": Character(
        id="elena",
        name="Dr. Elena Vex",
        title="Pattern Researcher",
        description="A renowned physicist who has studied Pattern Shaping for decades."
    ),
    "kai": Character(
        id="kai",
        name="Kai",
        title="Rival Shaper",
        description="Another Shaper who works for a competing organization."
    ),
    "overseer": Character(
        id="overseer",
        name="The Overseer",
        title="Master of the Void",
        description="A mysterious figure who controls the chaotic force behind the falling blocks."
    ),
}


@dataclass
class DialogueLine:
    """A single line of dialogue."""
    character_id: str
    text: str
    emotion: str = "neutral"  # neutral, happy, sad, angry, surprised


@dataclass
class StoryChapter:
    """
    Represents a single chapter in story mode.
    
    Each chapter has unique challenges and narrative.
    """
    id: int
    title: str
    description: str
    act: int = 1  # Act 1, 2, or 3
    
    # Gameplay modifiers
    target_score: int = 1000
    target_lines: int = 10
    time_limit: Optional[float] = None  # In seconds, None = no limit
    
    # Special rules
    special_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Narrative
    intro_dialogue: List[DialogueLine] = field(default_factory=list)
    outro_dialogue: List[DialogueLine] = field(default_factory=list)
    
    # Unlocks
    unlocks: List[str] = field(default_factory=list)
    
    # State
    completed: bool = False
    best_score: int = 0
    best_time: float = 0.0
    stars: int = 0  # 0-3 stars based on performance


# Story Chapters - Act I: Awakening
STORY_CHAPTERS = [
    StoryChapter(
        id=1,
        title="The Beginning",
        description="Strange visions lead to an unexpected awakening.",
        act=1,
        target_score=500,
        target_lines=5,
        intro_dialogue=[
            DialogueLine("alex", "These visions... they're getting stronger. Blocks falling, lines clearing... it feels so real.", "confused"),
            DialogueLine("alex", "What's happening to me?", "worried"),
        ],
        outro_dialogue=[
            DialogueLine("elena", "Impressive. You have the gift.", "pleased"),
            DialogueLine("alex", "Who are you? What just happened?", "surprised"),
            DialogueLine("elena", "All in due time. For now, know that you're not alone.", "calm"),
        ]
    ),
    StoryChapter(
        id=2,
        title="The Institute",
        description="Learn the basics at the Pattern Institute.",
        act=1,
        target_score=800,
        target_lines=8,
        intro_dialogue=[
            DialogueLine("elena", "Welcome to the Pattern Institute, Alex.", "welcoming"),
            DialogueLine("alex", "This place is incredible...", "amazed"),
            DialogueLine("elena", "Here you'll learn to control your abilities.", "informative"),
        ],
        outro_dialogue=[
            DialogueLine("elena", "Good progress. But this was just the beginning.", "encouraging"),
        ]
    ),
    StoryChapter(
        id=3,
        title="First Challenge",
        description="Stabilize a collapsing structure under pressure.",
        act=1,
        target_score=1000,
        target_lines=10,
        time_limit=120.0,
        intro_dialogue=[
            DialogueLine("elena", "Emergency! A building downtown is destabilizing!", "urgent"),
            DialogueLine("alex", "I'm not ready for this!", "scared"),
            DialogueLine("elena", "You must try. Lives are at stake.", "serious"),
        ],
        outro_dialogue=[
            DialogueLine("alex", "I... I did it.", "relieved"),
            DialogueLine("elena", "You're stronger than you know.", "proud"),
        ]
    ),
    StoryChapter(
        id=4,
        title="The Rival",
        description="A mysterious challenger appears.",
        act=1,
        target_score=1200,
        target_lines=12,
        intro_dialogue=[
            DialogueLine("kai", "So you're the new prodigy everyone's talking about.", "smug"),
            DialogueLine("alex", "Who are you?", "wary"),
            DialogueLine("kai", "The name's Kai. Let's see what you've got.", "challenging"),
        ],
        outro_dialogue=[
            DialogueLine("kai", "Not bad... for a beginner.", "impressed"),
            DialogueLine("alex", "Thanks... I think?", "confused"),
        ]
    ),
    StoryChapter(
        id=5,
        title="The Void Emerges",
        description="Face the chaotic power behind the falling blocks.",
        act=1,
        target_score=1500,
        target_lines=15,
        special_rules={"chaos_blocks": True},
        intro_dialogue=[
            DialogueLine("overseer", "So... a new Shaper arises.", "menacing"),
            DialogueLine("alex", "What is that?!", "terrified"),
            DialogueLine("elena", "The Overseer! Alex, be careful!", "alarmed"),
        ],
        outro_dialogue=[
            DialogueLine("overseer", "We will meet again, young Shaper.", "threatening"),
            DialogueLine("alex", "What was that thing?", "shaken"),
            DialogueLine("elena", "The greatest threat our world has ever known.", "grave"),
        ]
    ),
    # Act II chapters (6-15) - Training arc
    StoryChapter(
        id=6,
        title="Speed Training",
        description="Master the art of quick decisions.",
        act=2,
        target_score=1000,
        target_lines=10,
        time_limit=60.0,
        special_rules={"fast_drop": True},
    ),
    StoryChapter(
        id=7,
        title="Precision Patterns",
        description="Learn to create specific formations.",
        act=2,
        target_score=1200,
        target_lines=12,
        special_rules={"pattern_required": True},
    ),
    StoryChapter(
        id=8,
        title="The Long Blocks",
        description="Master the I-piece techniques.",
        act=2,
        target_score=1500,
        target_lines=15,
        special_rules={"i_piece_focus": True},
    ),
    # More chapters to be added...
]


class StoryManager:
    """
    Manages story mode progression.
    
    Handles chapter progression, dialogue, and story state.
    """
    
    def __init__(self, save_dir: str = "saves"):
        """Initialize story manager."""
        self._save_dir = save_dir
        self._chapters: List[StoryChapter] = list(STORY_CHAPTERS)
        self._current_chapter: Optional[StoryChapter] = None
        self._state = StoryState.NOT_STARTED
        self._total_progress = 0.0
        
        # Current dialogue state
        self._dialogue_index = 0
        self._in_dialogue = False
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """Get a character by ID."""
        return CHARACTERS.get(character_id)
    
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
                self._dialogue_index = 0
                self._in_dialogue = len(chapter.intro_dialogue) > 0
                return chapter
        return None
    
    def get_current_dialogue(self) -> Optional[DialogueLine]:
        """Get the current dialogue line."""
        if not self._current_chapter or not self._in_dialogue:
            return None
        
        dialogue_list = self._current_chapter.intro_dialogue
        if self._dialogue_index < len(dialogue_list):
            return dialogue_list[self._dialogue_index]
        return None
    
    def advance_dialogue(self) -> bool:
        """
        Advance to next dialogue line.
        
        Returns True if there's more dialogue, False if dialogue is complete.
        """
        if not self._current_chapter:
            return False
        
        self._dialogue_index += 1
        dialogue_list = self._current_chapter.intro_dialogue
        
        if self._dialogue_index >= len(dialogue_list):
            self._in_dialogue = False
            return False
        return True
    
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
        
        # Calculate stars (1-3 based on score)
        target = self._current_chapter.target_score
        if score >= target * 1.5:
            self._current_chapter.stars = 3
        elif score >= target * 1.2:
            self._current_chapter.stars = 2
        else:
            self._current_chapter.stars = 1
        
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
    
    def get_total_stars(self) -> int:
        """Get total stars earned across all chapters."""
        return sum(c.stars for c in self._chapters)
    
    def get_max_stars(self) -> int:
        """Get maximum possible stars."""
        return len(self._chapters) * 3
    
    def reset(self) -> None:
        """Reset all story progress."""
        for chapter in self._chapters:
            chapter.completed = False
            chapter.best_score = 0
            chapter.best_time = 0.0
            chapter.stars = 0
        
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
    
    @property
    def in_dialogue(self) -> bool:
        return self._in_dialogue
