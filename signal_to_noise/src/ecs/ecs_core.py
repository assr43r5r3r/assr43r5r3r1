"""
Lightweight Entity Component System (ECS) Core.

Provides a simple but effective ECS implementation optimized for game development.
Supports entity creation, component attachment, and efficient querying.
"""

from typing import Dict, List, Set, Type, TypeVar, Optional, Iterator, Any
from dataclasses import dataclass, field
import itertools


T = TypeVar('T')


class Entity:
    """
    Represents a unique entity in the game world.
    
    Entities are lightweight identifiers that can have components attached.
    """
    _id_counter = itertools.count(1)
    
    __slots__ = ['id', 'alive', 'tags']
    
    def __init__(self, entity_id: Optional[int] = None):
        self.id: int = entity_id if entity_id is not None else next(Entity._id_counter)
        self.alive: bool = True
        self.tags: Set[str] = set()
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        return self.id == other.id
    
    def __repr__(self) -> str:
        return f"Entity({self.id})"
    
    def add_tag(self, tag: str) -> 'Entity':
        """Add a tag to this entity."""
        self.tags.add(tag)
        return self
    
    def has_tag(self, tag: str) -> bool:
        """Check if entity has a specific tag."""
        return tag in self.tags
    
    def remove_tag(self, tag: str) -> 'Entity':
        """Remove a tag from this entity."""
        self.tags.discard(tag)
        return self


class World:
    """
    The World manages all entities and components.
    
    Provides methods for creating entities, attaching components,
    querying entities by component type, and running systems.
    """
    
    def __init__(self):
        self._entities: Dict[int, Entity] = {}
        # Component storage: component_type -> {entity_id -> component_instance}
        self._components: Dict[Type, Dict[int, Any]] = {}
        # Entity to component types mapping for fast lookup
        self._entity_components: Dict[int, Set[Type]] = {}
        # Pending entity removal
        self._pending_removal: List[int] = []
        # Systems registered with this world
        self._systems: List['System'] = []
        # Event listeners
        self._event_listeners: Dict[str, List[callable]] = {}
    
    def create_entity(self, *components, tags: Optional[List[str]] = None) -> Entity:
        """
        Create a new entity and optionally attach components.
        
        Args:
            *components: Variable number of component instances to attach
            tags: Optional list of tags to add to the entity
            
        Returns:
            The newly created Entity
        """
        entity = Entity()
        self._entities[entity.id] = entity
        self._entity_components[entity.id] = set()
        
        for component in components:
            self.add_component(entity, component)
        
        if tags:
            for tag in tags:
                entity.add_tag(tag)
        
        return entity
    
    def add_component(self, entity: Entity, component: Any) -> None:
        """
        Add a component to an entity.
        
        Args:
            entity: The entity to add the component to
            component: The component instance
        """
        component_type = type(component)
        
        if component_type not in self._components:
            self._components[component_type] = {}
        
        self._components[component_type][entity.id] = component
        self._entity_components[entity.id].add(component_type)
    
    def remove_component(self, entity: Entity, component_type: Type[T]) -> Optional[T]:
        """
        Remove a component from an entity.
        
        Args:
            entity: The entity to remove the component from
            component_type: The type of component to remove
            
        Returns:
            The removed component or None if not found
        """
        if component_type not in self._components:
            return None
        
        component = self._components[component_type].pop(entity.id, None)
        if component is not None and entity.id in self._entity_components:
            self._entity_components[entity.id].discard(component_type)
        
        return component
    
    def get_component(self, entity: Entity, component_type: Type[T]) -> Optional[T]:
        """
        Get a component from an entity.
        
        Args:
            entity: The entity to get the component from
            component_type: The type of component to get
            
        Returns:
            The component instance or None if not found
        """
        if component_type not in self._components:
            return None
        return self._components[component_type].get(entity.id)
    
    def has_component(self, entity: Entity, component_type: Type) -> bool:
        """Check if an entity has a specific component type."""
        if component_type not in self._components:
            return False
        return entity.id in self._components[component_type]
    
    def get_components(self, entity: Entity, *component_types: Type) -> tuple:
        """
        Get multiple components from an entity.
        
        Args:
            entity: The entity to get components from
            *component_types: Variable number of component types
            
        Returns:
            Tuple of component instances (may contain None for missing components)
        """
        return tuple(self.get_component(entity, ct) for ct in component_types)
    
    def query(self, *component_types: Type) -> Iterator[Entity]:
        """
        Query for entities that have all specified component types.
        
        Args:
            *component_types: Component types that entities must have
            
        Yields:
            Entities that have all specified component types
        """
        if not component_types:
            for entity in self._entities.values():
                if entity.alive:
                    yield entity
            return
        
        # Start with entities that have the first component type
        first_type = component_types[0]
        if first_type not in self._components:
            return
        
        candidate_ids = set(self._components[first_type].keys())
        
        # Intersect with entities that have other component types
        for component_type in component_types[1:]:
            if component_type not in self._components:
                return
            candidate_ids &= set(self._components[component_type].keys())
        
        for entity_id in candidate_ids:
            entity = self._entities.get(entity_id)
            if entity and entity.alive:
                yield entity
    
    def query_with_components(self, *component_types: Type) -> Iterator[tuple]:
        """
        Query for entities and their components.
        
        Args:
            *component_types: Component types to query for
            
        Yields:
            Tuples of (entity, component1, component2, ...)
        """
        for entity in self.query(*component_types):
            components = self.get_components(entity, *component_types)
            yield (entity,) + components
    
    def query_by_tag(self, tag: str) -> Iterator[Entity]:
        """Query for entities with a specific tag."""
        for entity in self._entities.values():
            if entity.alive and entity.has_tag(tag):
                yield entity
    
    def remove_entity(self, entity: Entity) -> None:
        """
        Mark an entity for removal. Actual removal happens during cleanup.
        
        Args:
            entity: The entity to remove
        """
        entity.alive = False
        self._pending_removal.append(entity.id)
    
    def cleanup(self) -> None:
        """Remove all pending entities and their components."""
        for entity_id in self._pending_removal:
            # Remove all components
            if entity_id in self._entity_components:
                for component_type in list(self._entity_components[entity_id]):
                    if component_type in self._components:
                        self._components[component_type].pop(entity_id, None)
                del self._entity_components[entity_id]
            
            # Remove entity
            self._entities.pop(entity_id, None)
        
        self._pending_removal.clear()
    
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Get an entity by its ID."""
        return self._entities.get(entity_id)
    
    def entity_count(self) -> int:
        """Get the number of alive entities."""
        return sum(1 for e in self._entities.values() if e.alive)
    
    def add_system(self, system: 'System') -> None:
        """Add a system to be processed."""
        system.world = self
        self._systems.append(system)
    
    def process_systems(self, dt: float) -> None:
        """Process all registered systems."""
        for system in self._systems:
            if system.enabled:
                system.process(dt)
    
    def emit_event(self, event_name: str, **data) -> None:
        """Emit an event to all registered listeners."""
        if event_name in self._event_listeners:
            for callback in self._event_listeners[event_name]:
                callback(**data)
    
    def on_event(self, event_name: str, callback: callable) -> None:
        """Register an event listener."""
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append(callback)
    
    def clear(self) -> None:
        """Clear all entities and components."""
        self._entities.clear()
        self._components.clear()
        self._entity_components.clear()
        self._pending_removal.clear()
        Entity._id_counter = itertools.count(1)


class System:
    """
    Base class for ECS systems.
    
    Systems contain game logic and operate on entities with specific components.
    """
    
    def __init__(self):
        self.world: Optional[World] = None
        self.enabled: bool = True
        self.priority: int = 0  # Lower priority runs first
    
    def process(self, dt: float) -> None:
        """
        Process the system for one frame.
        
        Args:
            dt: Delta time since last frame in seconds
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def on_add(self) -> None:
        """Called when the system is added to a world."""
        pass
    
    def on_remove(self) -> None:
        """Called when the system is removed from a world."""
        pass
