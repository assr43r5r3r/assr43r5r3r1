"""
Input handling for keyboard and gamepad.
"""

from typing import Dict, Set, Optional, Callable, List
from dataclasses import dataclass, field

try:
    import pygame
except ImportError:
    import pygame_ce as pygame

from .input_buffer import InputBuffer, DASState


@dataclass
class InputConfig:
    """Input configuration."""
    das_delay: int = 10  # Frames before auto-repeat
    arr_rate: int = 2    # Frames between auto-repeats
    soft_drop_rate: int = 2  # Frames per soft drop cell
    
    # Key bindings (pygame key constants as strings)
    bindings: Dict[str, str] = field(default_factory=lambda: {
        "move_left": "K_LEFT",
        "move_right": "K_RIGHT",
        "soft_drop": "K_DOWN",
        "hard_drop": "K_SPACE",
        "rotate_cw": "K_UP",
        "rotate_ccw": "K_z",
        "rotate_180": "K_a",
        "hold": "K_c",
        "pause": "K_ESCAPE",
        "restart": "K_r",
    })


class InputHandler:
    """
    Handles keyboard and gamepad input.
    
    Implements DAS/ARR for smooth movement and input buffering.
    """
    
    def __init__(self, config: InputConfig = None):
        """
        Initialize input handler.
        
        Args:
            config: Input configuration
        """
        self._config = config or InputConfig()
        
        # Key states
        self._keys_held: Set[int] = set()
        self._keys_pressed: Set[int] = set()
        self._keys_released: Set[int] = set()
        
        # DAS state for left/right movement
        self._das = DASState(
            delay=self._config.das_delay,
            rate=self._config.arr_rate
        )
        
        # Soft drop timing
        self._soft_drop_counter = 0
        
        # Input buffer for rotation and hard drop
        self._buffer = InputBuffer()
        
        # Action callbacks
        self._actions: Dict[str, Callable] = {}
        
        # Gamepad
        self._gamepad: Optional[pygame.joystick.Joystick] = None
        self._gamepad_enabled = True
        
        # Build key mapping
        self._key_map: Dict[int, str] = {}
        self._build_key_map()
        
        # Initialize gamepad
        self._init_gamepad()
    
    def _build_key_map(self) -> None:
        """Build key code to action mapping."""
        self._key_map.clear()
        
        for action, key_name in self._config.bindings.items():
            key_code = getattr(pygame, key_name, None)
            if key_code is not None:
                self._key_map[key_code] = action
    
    def _init_gamepad(self) -> None:
        """Initialize gamepad if available."""
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self._gamepad = pygame.joystick.Joystick(0)
            self._gamepad.init()
    
    def set_binding(self, action: str, key_name: str) -> None:
        """
        Set a key binding.
        
        Args:
            action: Action name
            key_name: Pygame key name (e.g., "K_LEFT")
        """
        self._config.bindings[action] = key_name
        self._build_key_map()
    
    def bind_action(self, action: str, callback: Callable) -> None:
        """
        Bind a callback to an action.
        
        Args:
            action: Action name
            callback: Function to call when action triggers
        """
        self._actions[action] = callback
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle a pygame event.
        
        Args:
            event: The pygame event
        """
        if event.type == pygame.KEYDOWN:
            self._keys_pressed.add(event.key)
            self._keys_held.add(event.key)
            
            # Get action for this key
            action = self._key_map.get(event.key)
            
            if action:
                # Buffer rotation and hard drop
                if action in ("rotate_cw", "rotate_ccw", "rotate_180", "hard_drop", "hold"):
                    self._buffer.buffer(action)
                
                # Start DAS for movement
                if action == "move_left":
                    self._das.start(-1)
                elif action == "move_right":
                    self._das.start(1)
        
        elif event.type == pygame.KEYUP:
            self._keys_released.add(event.key)
            self._keys_held.discard(event.key)
            
            action = self._key_map.get(event.key)
            
            if action:
                # Stop DAS when movement key released
                if action == "move_left" and self._das.direction == -1:
                    # Check if other direction is held
                    right_key = getattr(pygame, self._config.bindings.get("move_right", ""), None)
                    if right_key and right_key in self._keys_held:
                        self._das.start(1)
                    else:
                        self._das.stop()
                elif action == "move_right" and self._das.direction == 1:
                    left_key = getattr(pygame, self._config.bindings.get("move_left", ""), None)
                    if left_key and left_key in self._keys_held:
                        self._das.start(-1)
                    else:
                        self._das.stop()
    
    def update(self) -> None:
        """
        Update input state (call once per frame).
        
        Returns actions to execute based on current input state.
        """
        # Update buffer
        self._buffer.update()
        
        # Process buffered actions
        for action in ("rotate_cw", "rotate_ccw", "rotate_180", "hard_drop", "hold"):
            if self._buffer.consume(action):
                if action in self._actions:
                    self._actions[action]()
        
        # Process DAS movement
        if self._das.is_active:
            if self._das.update():
                if self._das.direction == -1 and "move_left" in self._actions:
                    self._actions["move_left"]()
                elif self._das.direction == 1 and "move_right" in self._actions:
                    self._actions["move_right"]()
        
        # Process soft drop
        soft_drop_key = getattr(pygame, self._config.bindings.get("soft_drop", ""), None)
        if soft_drop_key and soft_drop_key in self._keys_held:
            self._soft_drop_counter += 1
            if self._soft_drop_counter >= self._config.soft_drop_rate:
                self._soft_drop_counter = 0
                if "soft_drop" in self._actions:
                    self._actions["soft_drop"]()
        else:
            self._soft_drop_counter = 0
        
        # Clear frame-specific states
        self._keys_pressed.clear()
        self._keys_released.clear()
    
    def is_held(self, action: str) -> bool:
        """Check if an action's key is currently held."""
        key_name = self._config.bindings.get(action)
        if key_name:
            key_code = getattr(pygame, key_name, None)
            if key_code:
                return key_code in self._keys_held
        return False
    
    def was_pressed(self, action: str) -> bool:
        """Check if an action's key was just pressed this frame."""
        key_name = self._config.bindings.get(action)
        if key_name:
            key_code = getattr(pygame, key_name, None)
            if key_code:
                return key_code in self._keys_pressed
        return False
    
    def reset(self) -> None:
        """Reset input state."""
        self._keys_held.clear()
        self._keys_pressed.clear()
        self._keys_released.clear()
        self._das.reset()
        self._buffer.clear()
        self._soft_drop_counter = 0
    
    def update_config(self, das_delay: int = None, arr_rate: int = None,
                      soft_drop_rate: int = None) -> None:
        """Update timing configuration."""
        if das_delay is not None:
            self._config.das_delay = das_delay
            self._das.delay = das_delay
        if arr_rate is not None:
            self._config.arr_rate = arr_rate
            self._das.rate = arr_rate
        if soft_drop_rate is not None:
            self._config.soft_drop_rate = soft_drop_rate
    
    @property
    def gamepad_connected(self) -> bool:
        """Check if a gamepad is connected."""
        return self._gamepad is not None
