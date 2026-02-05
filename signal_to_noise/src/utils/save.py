"""
Save/Load system for game state persistence.

Provides deterministic serialization and deserialization of the complete
game state including entities, components, and world flags.
"""

import json
import os
import itertools
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
from dataclasses import asdict, is_dataclass

if TYPE_CHECKING:
    from ..ecs.ecs_core import Entity, World


def serialize_component(component: Any) -> Dict[str, Any]:
    """
    Serialize a component to a JSON-compatible dict.
    
    Args:
        component: Component instance (should be a dataclass)
        
    Returns:
        Dictionary representation of the component
    """
    if is_dataclass(component):
        data = asdict(component)
        data['_type'] = type(component).__name__
        return data
    elif hasattr(component, '__dict__'):
        data = component.__dict__.copy()
        data['_type'] = type(component).__name__
        return data
    else:
        return {'_type': type(component).__name__, 'value': str(component)}


def deserialize_component(data: Dict[str, Any], component_classes: Dict[str, type]) -> Optional[Any]:
    """
    Deserialize a component from a dict.
    
    Args:
        data: Dictionary with component data and _type field
        component_classes: Mapping of type names to component classes
        
    Returns:
        Reconstructed component instance or None
    """
    type_name = data.pop('_type', None)
    if type_name is None or type_name not in component_classes:
        return None
    
    component_class = component_classes[type_name]
    try:
        return component_class(**data)
    except TypeError:
        # Handle cases where data has extra fields
        import inspect
        sig = inspect.signature(component_class.__init__)
        valid_params = set(sig.parameters.keys()) - {'self'}
        filtered_data = {k: v for k, v in data.items() if k in valid_params}
        return component_class(**filtered_data)


def save_game(world: Any, 
              filepath: str,
              world_flags: Optional[Dict[str, Any]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Save the complete game state to a JSON file.
    
    Args:
        world: The ECS World instance
        filepath: Path to save file
        world_flags: Optional dictionary of world state flags
        metadata: Optional game metadata (playtime, act, etc.)
        
    Returns:
        True if save successful, False otherwise
    """
    try:
        save_data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'world_flags': world_flags or {},
            'entities': [],
            'components': {}
        }
        
        # Serialize all entities and their components
        for entity_id, entity in world._entities.items():
            if not entity.alive:
                continue
            
            entity_data = {
                'id': entity.id,
                'tags': list(entity.tags)
            }
            save_data['entities'].append(entity_data)
        
        # Serialize components by type
        for component_type, entities_components in world._components.items():
            type_name = component_type.__name__
            save_data['components'][type_name] = {}
            
            for entity_id, component in entities_components.items():
                # Only save components for alive entities
                if entity_id in world._entities and world._entities[entity_id].alive:
                    save_data['components'][type_name][str(entity_id)] = serialize_component(component)
        
        # Write to file
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"Save error: {e}")
        return False


def load_game(filepath: str, 
              world: Any,
              component_classes: Dict[str, type]) -> Optional[Dict[str, Any]]:
    """
    Load game state from a JSON file into a World instance.
    
    Args:
        filepath: Path to save file
        world: The ECS World instance to populate
        component_classes: Mapping of component type names to classes
        
    Returns:
        Dictionary with metadata and world_flags, or None on failure
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        
        # Clear existing world state
        world.clear()
        
        # Import Entity class dynamically to avoid circular imports
        # Get the Entity class from the world instance
        EntityClass = type(list(world._entities.values())[0]) if world._entities else None
        if EntityClass is None:
            # Fallback: create a simple entity-like class
            from ..ecs.ecs_core import Entity as EntityClass
        
        # Recreate entities
        entity_map: Dict[int, Any] = {}
        for entity_data in save_data.get('entities', []):
            entity = EntityClass(entity_id=entity_data['id'])
            entity.tags = set(entity_data.get('tags', []))
            
            world._entities[entity.id] = entity
            world._entity_components[entity.id] = set()
            entity_map[entity.id] = entity
        
        # Restore the ID counter to be higher than any loaded entity
        max_id = max(entity_map.keys()) if entity_map else 0
        EntityClass._id_counter = itertools.count(max_id + 1)
        
        # Recreate components
        for type_name, entities_components in save_data.get('components', {}).items():
            if type_name not in component_classes:
                continue
            
            for entity_id_str, component_data in entities_components.items():
                entity_id = int(entity_id_str)
                if entity_id not in entity_map:
                    continue
                
                component = deserialize_component(component_data.copy(), component_classes)
                if component:
                    world.add_component(entity_map[entity_id], component)
        
        return {
            'metadata': save_data.get('metadata', {}),
            'world_flags': save_data.get('world_flags', {}),
            'version': save_data.get('version', '1.0'),
            'timestamp': save_data.get('timestamp', '')
        }
        
    except Exception as e:
        print(f"Load error: {e}")
        return None


def get_save_files(save_dir: str) -> List[Dict[str, Any]]:
    """
    List all save files in a directory with their metadata.
    
    Args:
        save_dir: Directory containing save files
        
    Returns:
        List of dicts with filename and metadata
    """
    saves = []
    
    if not os.path.exists(save_dir):
        return saves
    
    for filename in os.listdir(save_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(save_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                saves.append({
                    'filename': filename,
                    'filepath': filepath,
                    'timestamp': data.get('timestamp', ''),
                    'metadata': data.get('metadata', {})
                })
            except Exception:
                pass
    
    # Sort by timestamp, newest first
    saves.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return saves


def create_snapshot(world: Any, world_flags: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create an in-memory snapshot of the current game state.
    
    Useful for undo functionality or state comparison.
    
    Args:
        world: The ECS World instance
        world_flags: Optional world state flags
        
    Returns:
        Complete state dictionary
    """
    snapshot = {
        'entities': [],
        'components': {},
        'world_flags': world_flags or {}
    }
    
    for entity_id, entity in world._entities.items():
        if entity.alive:
            snapshot['entities'].append({
                'id': entity.id,
                'tags': list(entity.tags)
            })
    
    for component_type, entities_components in world._components.items():
        type_name = component_type.__name__
        snapshot['components'][type_name] = {}
        
        for entity_id, component in entities_components.items():
            if entity_id in world._entities and world._entities[entity_id].alive:
                snapshot['components'][type_name][entity_id] = serialize_component(component)
    
    return snapshot


def restore_snapshot(snapshot: Dict[str, Any], 
                     world: Any,
                     component_classes: Dict[str, type]) -> bool:
    """
    Restore world state from a snapshot.
    
    Args:
        snapshot: State snapshot from create_snapshot
        world: The ECS World instance
        component_classes: Component type name to class mapping
        
    Returns:
        True if successful
    """
    try:
        world.clear()
        
        # Import Entity class dynamically
        try:
            from ..ecs.ecs_core import Entity as EntityClass
        except ImportError:
            # Fallback for test environments
            import sys
            signal_to_noise_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if signal_to_noise_path not in sys.path:
                sys.path.insert(0, signal_to_noise_path)
            from src.ecs.ecs_core import Entity as EntityClass
        
        entity_map = {}
        for entity_data in snapshot['entities']:
            entity = EntityClass(entity_id=entity_data['id'])
            entity.tags = set(entity_data.get('tags', []))
            world._entities[entity.id] = entity
            world._entity_components[entity.id] = set()
            entity_map[entity.id] = entity
        
        max_id = max(entity_map.keys()) if entity_map else 0
        EntityClass._id_counter = itertools.count(max_id + 1)
        
        for type_name, entities_components in snapshot['components'].items():
            if type_name not in component_classes:
                continue
            
            for entity_id, component_data in entities_components.items():
                entity_id = int(entity_id) if isinstance(entity_id, str) else entity_id
                if entity_id not in entity_map:
                    continue
                
                component = deserialize_component(component_data.copy(), component_classes)
                if component:
                    world.add_component(entity_map[entity_id], component)
        
        return True
        
    except Exception as e:
        print(f"Restore error: {e}")
        return False
