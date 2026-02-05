"""
Replay recording and playback system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum, auto
import json


class InputAction(Enum):
    """All possible input actions for replay."""
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    ROTATE_CW = auto()
    ROTATE_CCW = auto()
    ROTATE_180 = auto()
    HOLD = auto()


@dataclass
class FrameInput:
    """Input state for a single frame."""
    frame: int
    actions: List[InputAction] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "frame": self.frame,
            "actions": [a.name for a in self.actions]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FrameInput':
        return cls(
            frame=data["frame"],
            actions=[InputAction[a] for a in data["actions"]]
        )


@dataclass
class ReplayData:
    """Complete replay data."""
    seed: int
    start_level: int
    inputs: List[FrameInput] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "start_level": self.start_level,
            "inputs": [i.to_dict() for i in self.inputs],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReplayData':
        return cls(
            seed=data["seed"],
            start_level=data["start_level"],
            inputs=[FrameInput.from_dict(i) for i in data["inputs"]],
            metadata=data.get("metadata", {})
        )
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ReplayData':
        return cls.from_dict(json.loads(json_str))


class ReplayRecorder:
    """
    Records inputs for replay.
    """
    
    def __init__(self, seed: int, start_level: int = 1):
        self._data = ReplayData(seed=seed, start_level=start_level)
        self._current_frame = 0
        self._current_actions: List[InputAction] = []
    
    def record_action(self, action: InputAction) -> None:
        """Record an action for the current frame."""
        if action not in self._current_actions:
            self._current_actions.append(action)
    
    def end_frame(self) -> None:
        """Finalize the current frame and move to next."""
        if self._current_actions:
            self._data.inputs.append(FrameInput(
                frame=self._current_frame,
                actions=list(self._current_actions)
            ))
            self._current_actions.clear()
        self._current_frame += 1
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set replay metadata."""
        self._data.metadata[key] = value
    
    def get_replay(self) -> ReplayData:
        """Get the recorded replay data."""
        return self._data
    
    @property
    def frame(self) -> int:
        """Current frame number."""
        return self._current_frame


class ReplayPlayer:
    """
    Plays back recorded inputs.
    """
    
    def __init__(self, replay_data: ReplayData):
        self._data = replay_data
        self._current_frame = 0
        self._input_index = 0
    
    def get_actions(self, frame: int) -> List[InputAction]:
        """
        Get actions for a specific frame.
        
        Args:
            frame: Frame number to get actions for
        
        Returns:
            List of actions for that frame
        """
        if self._input_index >= len(self._data.inputs):
            return []
        
        current_input = self._data.inputs[self._input_index]
        if current_input.frame == frame:
            self._input_index += 1
            return current_input.actions
        
        return []
    
    def advance_frame(self) -> List[InputAction]:
        """
        Advance to next frame and return actions.
        
        Returns:
            List of actions for this frame
        """
        actions = self.get_actions(self._current_frame)
        self._current_frame += 1
        return actions
    
    def reset(self) -> None:
        """Reset playback to beginning."""
        self._current_frame = 0
        self._input_index = 0
    
    @property
    def seed(self) -> int:
        """Get the replay seed."""
        return self._data.seed
    
    @property
    def start_level(self) -> int:
        """Get the starting level."""
        return self._data.start_level
    
    @property
    def frame(self) -> int:
        """Current frame number."""
        return self._current_frame
    
    @property
    def is_finished(self) -> bool:
        """Check if replay has finished."""
        return self._input_index >= len(self._data.inputs)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get replay metadata."""
        return self._data.metadata
