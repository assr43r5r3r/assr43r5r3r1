"""
Stage system for the Tetris game.
Replaces level system with 25 stages that progress based on score.
"""

from typing import Dict, Tuple, List
from dataclasses import dataclass


@dataclass
class StageConfig:
    """Configuration for a single stage."""
    stage_number: int
    name: str
    score_threshold: int  # Score needed to reach this stage
    gravity_frames: int  # Frames per cell drop (lower = faster)
    
    # Visual theme
    background_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    particle_intensity: float  # 0.0 to 2.0
    glow_intensity: float  # 0.0 to 1.0
    shake_multiplier: float  # Screen shake multiplier
    
    # Special effects
    has_trails: bool = False
    has_pulse: bool = False
    has_lightning: bool = False


# Define all 25 stages
STAGES: Dict[int, StageConfig] = {
    1: StageConfig(
        stage_number=1,
        name="Beginner",
        score_threshold=0,
        gravity_frames=48,
        background_color=(20, 20, 30),
        accent_color=(100, 200, 255),
        particle_intensity=0.5,
        glow_intensity=0.3,
        shake_multiplier=0.5,
    ),
    2: StageConfig(
        stage_number=2,
        name="Warmup",
        score_threshold=100,
        gravity_frames=44,
        background_color=(20, 25, 35),
        accent_color=(100, 210, 255),
        particle_intensity=0.6,
        glow_intensity=0.35,
        shake_multiplier=0.55,
    ),
    3: StageConfig(
        stage_number=3,
        name="Getting Started",
        score_threshold=250,
        gravity_frames=40,
        background_color=(22, 28, 38),
        accent_color=(110, 220, 255),
        particle_intensity=0.7,
        glow_intensity=0.4,
        shake_multiplier=0.6,
    ),
    4: StageConfig(
        stage_number=4,
        name="Novice",
        score_threshold=450,
        gravity_frames=36,
        background_color=(25, 30, 40),
        accent_color=(120, 230, 255),
        particle_intensity=0.75,
        glow_intensity=0.45,
        shake_multiplier=0.65,
    ),
    5: StageConfig(
        stage_number=5,
        name="Amateur",
        score_threshold=700,
        gravity_frames=32,
        background_color=(28, 32, 45),
        accent_color=(130, 240, 255),
        particle_intensity=0.8,
        glow_intensity=0.5,
        shake_multiplier=0.7,
        has_trails=True,
    ),
    6: StageConfig(
        stage_number=6,
        name="Intermediate",
        score_threshold=1000,
        gravity_frames=28,
        background_color=(30, 35, 50),
        accent_color=(150, 200, 255),
        particle_intensity=0.85,
        glow_intensity=0.55,
        shake_multiplier=0.75,
        has_trails=True,
    ),
    7: StageConfig(
        stage_number=7,
        name="Rising",
        score_threshold=1350,
        gravity_frames=25,
        background_color=(32, 38, 55),
        accent_color=(160, 180, 255),
        particle_intensity=0.9,
        glow_intensity=0.6,
        shake_multiplier=0.8,
        has_trails=True,
    ),
    8: StageConfig(
        stage_number=8,
        name="Skilled",
        score_threshold=1750,
        gravity_frames=22,
        background_color=(35, 35, 60),
        accent_color=(180, 160, 255),
        particle_intensity=0.95,
        glow_intensity=0.65,
        shake_multiplier=0.85,
        has_trails=True,
    ),
    9: StageConfig(
        stage_number=9,
        name="Advanced",
        score_threshold=2200,
        gravity_frames=19,
        background_color=(38, 30, 65),
        accent_color=(200, 140, 255),
        particle_intensity=1.0,
        glow_intensity=0.7,
        shake_multiplier=0.9,
        has_trails=True,
        has_pulse=True,
    ),
    10: StageConfig(
        stage_number=10,
        name="Expert",
        score_threshold=2700,
        gravity_frames=16,
        background_color=(40, 28, 70),
        accent_color=(220, 120, 255),
        particle_intensity=1.1,
        glow_intensity=0.75,
        shake_multiplier=0.95,
        has_trails=True,
        has_pulse=True,
    ),
    11: StageConfig(
        stage_number=11,
        name="Elite",
        score_threshold=3250,
        gravity_frames=14,
        background_color=(42, 25, 75),
        accent_color=(255, 100, 200),
        particle_intensity=1.15,
        glow_intensity=0.8,
        shake_multiplier=1.0,
        has_trails=True,
        has_pulse=True,
    ),
    12: StageConfig(
        stage_number=12,
        name="Master",
        score_threshold=3850,
        gravity_frames=12,
        background_color=(45, 22, 80),
        accent_color=(255, 80, 180),
        particle_intensity=1.2,
        glow_intensity=0.85,
        shake_multiplier=1.05,
        has_trails=True,
        has_pulse=True,
    ),
    13: StageConfig(
        stage_number=13,
        name="Grandmaster",
        score_threshold=4500,
        gravity_frames=10,
        background_color=(50, 20, 70),
        accent_color=(255, 100, 150),
        particle_intensity=1.25,
        glow_intensity=0.9,
        shake_multiplier=1.1,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    14: StageConfig(
        stage_number=14,
        name="Champion",
        score_threshold=5200,
        gravity_frames=9,
        background_color=(55, 18, 65),
        accent_color=(255, 120, 120),
        particle_intensity=1.3,
        glow_intensity=0.92,
        shake_multiplier=1.15,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    15: StageConfig(
        stage_number=15,
        name="Legend",
        score_threshold=6000,
        gravity_frames=8,
        background_color=(60, 15, 55),
        accent_color=(255, 150, 100),
        particle_intensity=1.35,
        glow_intensity=0.95,
        shake_multiplier=1.2,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    16: StageConfig(
        stage_number=16,
        name="Mythic",
        score_threshold=6900,
        gravity_frames=7,
        background_color=(65, 12, 45),
        accent_color=(255, 180, 80),
        particle_intensity=1.4,
        glow_intensity=1.0,
        shake_multiplier=1.25,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    17: StageConfig(
        stage_number=17,
        name="Celestial",
        score_threshold=7900,
        gravity_frames=6,
        background_color=(70, 10, 35),
        accent_color=(255, 200, 60),
        particle_intensity=1.45,
        glow_intensity=1.0,
        shake_multiplier=1.3,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    18: StageConfig(
        stage_number=18,
        name="Divine",
        score_threshold=9000,
        gravity_frames=5,
        background_color=(75, 8, 25),
        accent_color=(255, 220, 40),
        particle_intensity=1.5,
        glow_intensity=1.0,
        shake_multiplier=1.35,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    19: StageConfig(
        stage_number=19,
        name="Immortal",
        score_threshold=10200,
        gravity_frames=4,
        background_color=(80, 5, 15),
        accent_color=(255, 240, 100),
        particle_intensity=1.6,
        glow_intensity=1.0,
        shake_multiplier=1.4,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    20: StageConfig(
        stage_number=20,
        name="Transcendent",
        score_threshold=11500,
        gravity_frames=3,
        background_color=(85, 3, 10),
        accent_color=(255, 255, 150),
        particle_intensity=1.7,
        glow_intensity=1.0,
        shake_multiplier=1.45,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    21: StageConfig(
        stage_number=21,
        name="Ascended",
        score_threshold=13000,
        gravity_frames=3,
        background_color=(90, 0, 5),
        accent_color=(255, 255, 200),
        particle_intensity=1.8,
        glow_intensity=1.0,
        shake_multiplier=1.5,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    22: StageConfig(
        stage_number=22,
        name="Godlike",
        score_threshold=14600,
        gravity_frames=2,
        background_color=(95, 0, 0),
        accent_color=(255, 220, 220),
        particle_intensity=1.85,
        glow_intensity=1.0,
        shake_multiplier=1.55,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    23: StageConfig(
        stage_number=23,
        name="Eternal",
        score_threshold=16400,
        gravity_frames=2,
        background_color=(100, 5, 5),
        accent_color=(255, 200, 200),
        particle_intensity=1.9,
        glow_intensity=1.0,
        shake_multiplier=1.6,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    24: StageConfig(
        stage_number=24,
        name="Infinite",
        score_threshold=18500,
        gravity_frames=2,
        background_color=(110, 10, 10),
        accent_color=(255, 180, 180),
        particle_intensity=1.95,
        glow_intensity=1.0,
        shake_multiplier=1.65,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
    25: StageConfig(
        stage_number=25,
        name="Ultimate",
        score_threshold=21000,
        gravity_frames=1,
        background_color=(120, 15, 15),
        accent_color=(255, 150, 150),
        particle_intensity=2.0,
        glow_intensity=1.0,
        shake_multiplier=1.7,
        has_trails=True,
        has_pulse=True,
        has_lightning=True,
    ),
}


class StageManager:
    """
    Manages stage progression and effects.
    """
    
    def __init__(self):
        """Initialize stage manager."""
        self._current_stage = 1
        self._score = 0
        self._transition_progress = 0.0  # 0.0 to 1.0 during transitions
        self._in_transition = False
        self._transition_from = 1
        self._transition_to = 1
    
    def get_stage_for_score(self, score: int) -> int:
        """Get the stage number for a given score."""
        stage = 1
        for stage_num, config in sorted(STAGES.items()):
            if score >= config.score_threshold:
                stage = stage_num
            else:
                break
        return min(stage, 25)
    
    def update_score(self, score: int) -> bool:
        """
        Update score and check for stage change.
        
        Args:
            score: Current score
            
        Returns:
            True if stage changed
        """
        self._score = score
        new_stage = self.get_stage_for_score(score)
        
        if new_stage != self._current_stage:
            self._transition_from = self._current_stage
            self._transition_to = new_stage
            self._current_stage = new_stage
            self._in_transition = True
            self._transition_progress = 0.0
            return True
        
        return False
    
    def update_transition(self, dt: float) -> None:
        """
        Update stage transition animation.
        
        Args:
            dt: Delta time in seconds
        """
        if self._in_transition:
            self._transition_progress += dt * 2.0  # 0.5 second transition
            if self._transition_progress >= 1.0:
                self._transition_progress = 1.0
                self._in_transition = False
    
    def get_current_config(self) -> StageConfig:
        """Get current stage configuration."""
        return STAGES.get(self._current_stage, STAGES[1])
    
    def get_gravity(self) -> int:
        """Get current gravity (frames per drop)."""
        return self.get_current_config().gravity_frames
    
    def get_score_to_next(self) -> int:
        """Get score needed for next stage."""
        if self._current_stage >= 25:
            return 0
        next_config = STAGES.get(self._current_stage + 1)
        if next_config:
            return next_config.score_threshold - self._score
        return 0
    
    def reset(self) -> None:
        """Reset to stage 1."""
        self._current_stage = 1
        self._score = 0
        self._in_transition = False
        self._transition_progress = 0.0
    
    @property
    def current_stage(self) -> int:
        return self._current_stage
    
    @property
    def stage_name(self) -> str:
        return self.get_current_config().name
    
    @property
    def in_transition(self) -> bool:
        return self._in_transition
    
    @property
    def transition_progress(self) -> float:
        return self._transition_progress
    
    @property
    def max_stage(self) -> int:
        return 25
