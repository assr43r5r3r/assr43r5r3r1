"""
Particle system with object pooling.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field
import random
import math

try:
    import pygame
except ImportError:
    import pygame_ce as pygame

from src.util.pool import ObjectPool
from src.util.math_utils import lerp, ease_out_quad


@dataclass
class Particle:
    """A single particle."""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    life: float = 1.0
    max_life: float = 1.0
    size: float = 4.0
    color: Tuple[int, int, int] = (255, 255, 255)
    gravity: float = 0.0
    friction: float = 0.98
    fade: bool = True
    shrink: bool = True
    
    def reset(self) -> None:
        """Reset particle to initial state."""
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 1.0
        self.max_life = 1.0
        self.size = 4.0
        self.color = (255, 255, 255)
        self.gravity = 0.0
        self.friction = 0.98
        self.fade = True
        self.shrink = True
    
    def update(self, dt: float) -> bool:
        """
        Update particle.
        
        Returns:
            False if particle is dead
        """
        self.life -= dt
        if self.life <= 0:
            return False
        
        # Apply physics
        self.vy += self.gravity * dt * 60
        self.vx *= self.friction
        self.vy *= self.friction
        
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        
        return True
    
    @property
    def alpha(self) -> int:
        """Get current alpha based on life."""
        if not self.fade:
            return 255
        return int(255 * (self.life / self.max_life))
    
    @property
    def current_size(self) -> float:
        """Get current size based on life."""
        if not self.shrink:
            return self.size
        return self.size * (self.life / self.max_life)


class ParticleEmitter:
    """Configuration for particle emission."""
    
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        count: int = 10,
        speed_min: float = 1,
        speed_max: float = 5,
        angle_min: float = 0,
        angle_max: float = 360,
        life_min: float = 0.5,
        life_max: float = 1.0,
        size_min: float = 3,
        size_max: float = 6,
        color: Tuple[int, int, int] = (255, 255, 255),
        gravity: float = 0.2,
        friction: float = 0.98,
        fade: bool = True,
        shrink: bool = True
    ):
        self.x = x
        self.y = y
        self.count = count
        self.speed_min = speed_min
        self.speed_max = speed_max
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.life_min = life_min
        self.life_max = life_max
        self.size_min = size_min
        self.size_max = size_max
        self.color = color
        self.gravity = gravity
        self.friction = friction
        self.fade = fade
        self.shrink = shrink


class ParticleSystem:
    """
    Particle system with object pooling.
    
    Manages creation, updating, and rendering of particles.
    """
    
    def __init__(self, pool_size: int = 500):
        """
        Initialize particle system.
        
        Args:
            pool_size: Maximum number of particles
        """
        self._pool = ObjectPool(
            factory=Particle,
            reset_fn=lambda p: p.reset(),
            initial_size=pool_size
        )
        self._active_particles: List[Particle] = []
        self._rng = random.Random()
    
    def emit(self, emitter: ParticleEmitter) -> None:
        """
        Emit particles from an emitter.
        
        Args:
            emitter: Particle emitter configuration
        """
        for _ in range(emitter.count):
            particle = self._pool.acquire()
            
            # Random angle and speed
            angle = self._rng.uniform(emitter.angle_min, emitter.angle_max)
            speed = self._rng.uniform(emitter.speed_min, emitter.speed_max)
            
            # Convert angle to radians
            rad = math.radians(angle)
            
            particle.x = emitter.x
            particle.y = emitter.y
            particle.vx = math.cos(rad) * speed
            particle.vy = math.sin(rad) * speed
            
            particle.life = self._rng.uniform(emitter.life_min, emitter.life_max)
            particle.max_life = particle.life
            
            particle.size = self._rng.uniform(emitter.size_min, emitter.size_max)
            particle.color = emitter.color
            particle.gravity = emitter.gravity
            particle.friction = emitter.friction
            particle.fade = emitter.fade
            particle.shrink = emitter.shrink
            
            self._active_particles.append(particle)
    
    def emit_line_clear(self, y: int, cell_size: int, grid_x: int, 
                        grid_width: int, color: Tuple[int, int, int]) -> None:
        """
        Emit particles for a line clear.
        
        Args:
            y: Grid Y position of cleared line
            cell_size: Size of each cell in pixels
            grid_x: X offset of grid in pixels
            grid_width: Width of grid in cells
            color: Particle color
        """
        pixel_y = y * cell_size + cell_size // 2
        
        for x in range(grid_width):
            pixel_x = grid_x + x * cell_size + cell_size // 2
            
            emitter = ParticleEmitter(
                x=pixel_x,
                y=pixel_y,
                count=5,
                speed_min=2,
                speed_max=6,
                angle_min=-90,
                angle_max=90,
                life_min=0.3,
                life_max=0.6,
                size_min=3,
                size_max=7,
                color=color,
                gravity=0.3
            )
            self.emit(emitter)
    
    def emit_hard_drop(self, x: int, y: int, cell_size: int, 
                       grid_x: int, piece_width: int,
                       color: Tuple[int, int, int]) -> None:
        """
        Emit particles for a hard drop.
        
        Args:
            x: Grid X position
            y: Grid Y position
            cell_size: Size of each cell
            grid_x: X offset of grid
            piece_width: Width of piece in cells
            color: Particle color
        """
        pixel_y = y * cell_size
        
        for i in range(piece_width):
            pixel_x = grid_x + (x + i) * cell_size + cell_size // 2
            
            emitter = ParticleEmitter(
                x=pixel_x,
                y=pixel_y,
                count=3,
                speed_min=1,
                speed_max=3,
                angle_min=180,
                angle_max=360,
                life_min=0.2,
                life_max=0.4,
                size_min=2,
                size_max=5,
                color=color,
                gravity=-0.1
            )
            self.emit(emitter)
    
    def emit_tspin(self, x: int, y: int, cell_size: int,
                   grid_x: int, color: Tuple[int, int, int]) -> None:
        """
        Emit particles for a T-Spin.
        
        Args:
            x: Grid X position (center)
            y: Grid Y position (center)
            cell_size: Size of each cell
            grid_x: X offset of grid
            color: Particle color
        """
        pixel_x = grid_x + x * cell_size + cell_size // 2
        pixel_y = y * cell_size + cell_size // 2
        
        # Radial burst
        emitter = ParticleEmitter(
            x=pixel_x,
            y=pixel_y,
            count=30,
            speed_min=3,
            speed_max=8,
            angle_min=0,
            angle_max=360,
            life_min=0.4,
            life_max=0.8,
            size_min=4,
            size_max=8,
            color=color,
            gravity=0.1
        )
        self.emit(emitter)
    
    def update(self, dt: float) -> None:
        """
        Update all particles.
        
        Args:
            dt: Delta time in seconds
        """
        dead_particles = []
        
        for particle in self._active_particles:
            if not particle.update(dt):
                dead_particles.append(particle)
        
        # Return dead particles to pool
        for particle in dead_particles:
            self._active_particles.remove(particle)
            self._pool.release(particle)
    
    def draw(self, surface: pygame.Surface, offset_x: int = 0, 
             offset_y: int = 0) -> None:
        """
        Draw all particles.
        
        Args:
            surface: Surface to draw on
            offset_x: X offset (for screen shake)
            offset_y: Y offset (for screen shake)
        """
        for particle in self._active_particles:
            size = int(particle.current_size)
            if size < 1:
                continue
            
            alpha = particle.alpha
            color = (*particle.color, alpha)
            
            # Create a small surface for the particle
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surface,
                color,
                (size, size),
                size
            )
            
            surface.blit(
                particle_surface,
                (int(particle.x) - size + offset_x,
                 int(particle.y) - size + offset_y)
            )
    
    def clear(self) -> None:
        """Remove all particles."""
        for particle in self._active_particles:
            self._pool.release(particle)
        self._active_particles.clear()
    
    @property
    def count(self) -> int:
        """Number of active particles."""
        return len(self._active_particles)
