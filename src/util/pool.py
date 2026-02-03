"""
Object pooling system to avoid per-frame allocations.
"""

from typing import TypeVar, Generic, Callable, List, Optional

T = TypeVar('T')


class ObjectPool(Generic[T]):
    """
    Generic object pool for reusing objects and avoiding allocations.
    Used primarily for particles and other frequently created/destroyed objects.
    """
    
    def __init__(self, factory: Callable[[], T], reset_fn: Callable[[T], None], 
                 initial_size: int = 100):
        """
        Initialize the object pool.
        
        Args:
            factory: Function to create new objects
            reset_fn: Function to reset an object to initial state
            initial_size: Number of objects to pre-allocate
        """
        self._factory = factory
        self._reset_fn = reset_fn
        self._available: List[T] = []
        self._in_use: List[T] = []
        
        # Pre-allocate objects
        for _ in range(initial_size):
            self._available.append(factory())
    
    def acquire(self) -> T:
        """
        Get an object from the pool.
        Creates a new one if pool is empty.
        """
        if self._available:
            obj = self._available.pop()
        else:
            obj = self._factory()
        
        self._in_use.append(obj)
        return obj
    
    def release(self, obj: T) -> None:
        """
        Return an object to the pool.
        """
        if obj in self._in_use:
            self._in_use.remove(obj)
            self._reset_fn(obj)
            self._available.append(obj)
    
    def release_all(self) -> None:
        """
        Return all in-use objects to the pool.
        """
        for obj in self._in_use:
            self._reset_fn(obj)
            self._available.append(obj)
        self._in_use.clear()
    
    @property
    def active_count(self) -> int:
        """Number of objects currently in use."""
        return len(self._in_use)
    
    @property
    def available_count(self) -> int:
        """Number of objects available in pool."""
        return len(self._available)
    
    def get_active(self) -> List[T]:
        """Get list of all active objects (copy)."""
        return list(self._in_use)
