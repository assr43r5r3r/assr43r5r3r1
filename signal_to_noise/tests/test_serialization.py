"""
Unit tests for save/load serialization.
"""

import pytest
import json
import tempfile
import os
import sys

# Add the signal_to_noise directory to path
signal_to_noise_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, signal_to_noise_dir)

from src.ecs.ecs_core import World, Entity
from src.ecs.components import (
    Position, Renderable, NetworkNode, NetworkLink, 
    Message, Signal, Faction, Timer
)
from src.utils.save import (
    serialize_component, deserialize_component,
    save_game, load_game, create_snapshot, restore_snapshot
)


# Component classes map for deserialization
COMPONENT_CLASSES = {
    'Position': Position,
    'Renderable': Renderable,
    'NetworkNode': NetworkNode,
    'NetworkLink': NetworkLink,
    'Message': Message,
    'Signal': Signal,
    'Faction': Faction,
    'Timer': Timer
}


class TestComponentSerialization:
    """Tests for component serialization."""
    
    def test_serialize_position(self):
        """Test Position component serialization."""
        pos = Position(x=100.5, y=200.75)
        data = serialize_component(pos)
        
        assert data['_type'] == 'Position'
        assert data['x'] == 100.5
        assert data['y'] == 200.75
    
    def test_serialize_network_node(self):
        """Test NetworkNode component serialization."""
        node = NetworkNode(
            node_id='test_node',
            name='Test Node',
            capacity=8192,
            trust=0.8,
            owner='TestFaction'
        )
        data = serialize_component(node)
        
        assert data['_type'] == 'NetworkNode'
        assert data['node_id'] == 'test_node'
        assert data['name'] == 'Test Node'
        assert data['capacity'] == 8192
        assert data['trust'] == 0.8
        assert data['owner'] == 'TestFaction'
    
    def test_serialize_message(self):
        """Test Message component serialization."""
        msg = Message(
            msg_id='M001',
            origin='A',
            dest='B',
            tag='trade',
            priority=7,
            size=2048,
            reward=50,
            content_snippet='Test message content'
        )
        data = serialize_component(msg)
        
        assert data['_type'] == 'Message'
        assert data['msg_id'] == 'M001'
        assert data['origin'] == 'A'
        assert data['dest'] == 'B'
        assert data['priority'] == 7
    
    def test_deserialize_position(self):
        """Test Position component deserialization."""
        data = {'_type': 'Position', 'x': 150.0, 'y': 250.0}
        pos = deserialize_component(data, COMPONENT_CLASSES)
        
        assert isinstance(pos, Position)
        assert pos.x == 150.0
        assert pos.y == 250.0
    
    def test_deserialize_network_node(self):
        """Test NetworkNode component deserialization."""
        data = {
            '_type': 'NetworkNode',
            'node_id': 'test',
            'name': 'Test',
            'capacity': 4096,
            'trust': 0.5,
            'owner': None,
            'buffer': [],
            'stats': {},
            'node_type': 'relay'
        }
        node = deserialize_component(data, COMPONENT_CLASSES)
        
        assert isinstance(node, NetworkNode)
        assert node.node_id == 'test'
        assert node.capacity == 4096
    
    def test_roundtrip_serialization(self):
        """Test that serialize/deserialize is lossless."""
        original = Position(x=123.456, y=789.012)
        data = serialize_component(original)
        restored = deserialize_component(data, COMPONENT_CLASSES)
        
        assert restored.x == original.x
        assert restored.y == original.y


class TestSaveLoad:
    """Tests for full game save/load."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.world = World()
    
    def test_save_empty_world(self):
        """Test saving an empty world."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            result = save_game(self.world, filepath)
            assert result == True
            assert os.path.exists(filepath)
            
            # Verify file content
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert 'version' in data
            assert 'entities' in data
            assert 'components' in data
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_save_world_with_entities(self):
        """Test saving a world with entities."""
        # Create some entities
        self.world.create_entity(
            Position(x=100, y=200),
            NetworkNode(node_id='A', name='Node A', capacity=4096, trust=0.8)
        )
        self.world.create_entity(
            Position(x=300, y=400),
            NetworkNode(node_id='B', name='Node B', capacity=8192, trust=0.6)
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            result = save_game(self.world, filepath)
            assert result == True
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert len(data['entities']) == 2
            assert 'Position' in data['components']
            assert 'NetworkNode' in data['components']
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_load_world(self):
        """Test loading a saved world."""
        # Create and save
        entity1 = self.world.create_entity(
            Position(x=100, y=200),
            NetworkNode(node_id='A', name='Node A', capacity=4096, trust=0.8)
        )
        entity1.add_tag('test_tag')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            save_game(self.world, filepath)
            
            # Load into new world
            new_world = World()
            result = load_game(filepath, new_world, COMPONENT_CLASSES)
            
            assert result is not None
            assert new_world.entity_count() == 1
            
            # Verify components were restored
            for entity in new_world.query(Position, NetworkNode):
                pos = new_world.get_component(entity, Position)
                node = new_world.get_component(entity, NetworkNode)
                
                assert pos.x == 100
                assert pos.y == 200
                assert node.node_id == 'A'
                assert entity.has_tag('test_tag')
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_save_with_metadata(self):
        """Test saving with metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            metadata = {'playtime': 3600, 'act': 2, 'difficulty': 'hard'}
            world_flags = {'colony_fallen': True, 'archive_unlocked': False}
            
            save_game(self.world, filepath, world_flags=world_flags, metadata=metadata)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert data['metadata']['playtime'] == 3600
            assert data['metadata']['act'] == 2
            assert data['world_flags']['colony_fallen'] == True
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_load_returns_metadata(self):
        """Test that loading returns metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            metadata = {'playtime': 1800}
            world_flags = {'test_flag': True}
            
            save_game(self.world, filepath, world_flags=world_flags, metadata=metadata)
            
            new_world = World()
            result = load_game(filepath, new_world, COMPONENT_CLASSES)
            
            assert result['metadata']['playtime'] == 1800
            assert result['world_flags']['test_flag'] == True
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)


class TestSnapshot:
    """Tests for in-memory snapshots."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.world = World()
    
    def test_create_snapshot(self):
        """Test creating an in-memory snapshot."""
        self.world.create_entity(Position(x=50, y=100))
        
        snapshot = create_snapshot(self.world)
        
        assert 'entities' in snapshot
        assert 'components' in snapshot
        assert len(snapshot['entities']) == 1
    
    def test_restore_snapshot(self):
        """Test restoring from a snapshot."""
        # Create initial state
        self.world.create_entity(
            Position(x=50, y=100),
            NetworkNode(node_id='X', name='Node X', capacity=1024, trust=0.5)
        )
        
        snapshot = create_snapshot(self.world)
        
        # Modify world
        self.world.clear()
        assert self.world.entity_count() == 0
        
        # Restore
        result = restore_snapshot(snapshot, self.world, COMPONENT_CLASSES)
        
        assert result == True
        assert self.world.entity_count() == 1
        
        for entity in self.world.query(Position):
            pos = self.world.get_component(entity, Position)
            assert pos.x == 50
            assert pos.y == 100


class TestSaveLoadRoundTrip:
    """Integration tests for full save/load cycles."""
    
    def test_complete_roundtrip(self):
        """Test a complete save/load roundtrip with complex data."""
        world = World()
        
        # Create nodes
        world.create_entity(
            Position(x=100, y=200),
            NetworkNode(node_id='A', name='Harbor', capacity=10240, trust=0.8, owner=None)
        )
        world.create_entity(
            Position(x=300, y=150),
            NetworkNode(node_id='B', name='Market', capacity=8192, trust=0.7, owner='Market')
        )
        
        # Create link
        world.create_entity(
            NetworkLink(a='A', b='B', bandwidth=2048, latency=0.1, reliability=0.95, base_risk=0.05)
        )
        
        # Create message
        world.create_entity(
            Message(msg_id='M001', origin='A', dest='B', tag='trade', priority=5, size=1024, reward=20)
        )
        
        # Create faction
        world.create_entity(
            Faction(faction_id='Market', reputation=25, resources=150)
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            # Save
            world_flags = {'test_event_triggered': True}
            save_game(world, filepath, world_flags=world_flags)
            
            # Load into new world
            new_world = World()
            result = load_game(filepath, new_world, COMPONENT_CLASSES)
            
            # Verify counts
            assert new_world.entity_count() == 5
            
            # Verify nodes
            node_count = sum(1 for _ in new_world.query(NetworkNode))
            assert node_count == 2
            
            # Verify link
            link_count = sum(1 for _ in new_world.query(NetworkLink))
            assert link_count == 1
            
            # Verify message
            for entity, msg in new_world.query_with_components(Message):
                assert msg.msg_id == 'M001'
                assert msg.origin == 'A'
                assert msg.dest == 'B'
            
            # Verify world flags
            assert result['world_flags']['test_event_triggered'] == True
            
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
