"""
Integration tests for end-to-end game scenarios.
"""

import pytest
import sys
import os

# Add the signal_to_noise directory to path
signal_to_noise_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, signal_to_noise_dir)

from src.ecs.ecs_core import World
from src.ecs.components import (
    Position, NetworkNode, NetworkLink, Message, Signal, Faction
)
from src.ecs.systems.network_system import NetworkSystem
from src.ecs.systems.routing_system import RoutingSystem
from src.ecs.systems.bandwidth_system import BandwidthSystem
from src.ecs.systems.signal_system import SignalSystem


class TestMessageDeliveryScenario:
    """Integration tests for message delivery scenarios."""
    
    def setup_method(self):
        """Set up test world and systems."""
        self.world = World()
        
        # Initialize systems
        self.network_system = NetworkSystem()
        self.network_system.world = self.world
        
        self.routing_system = RoutingSystem()
        self.routing_system.world = self.world
        
        self.bandwidth_system = BandwidthSystem()
        self.bandwidth_system.world = self.world
        
        self.signal_system = SignalSystem()
        self.signal_system.world = self.world
        
        # Create test network
        self._create_network()
        
        # Create factions
        self._create_factions()
        
        # Track events
        self.delivered_messages = []
        self.intercepted_messages = []
        
        self.world.on_event('message_delivered', self._on_delivered)
        self.world.on_event('message_intercepted', self._on_intercepted)
    
    def _create_network(self):
        """Create a test network."""
        # Nodes
        nodes_data = [
            ('A', 100, 200, 0.8),
            ('B', 300, 150, 0.7),
            ('C', 250, 350, 0.6),
            ('D', 500, 200, 0.9)
        ]
        
        for node_id, x, y, trust in nodes_data:
            self.world.create_entity(
                Position(x=x, y=y),
                NetworkNode(node_id=node_id, name=node_id, capacity=8192, trust=trust)
            )
        
        # Links
        links_data = [
            ('A', 'B', 2048, 0.1, 0.95, 0.05),
            ('B', 'C', 1536, 0.15, 0.85, 0.1),
            ('B', 'D', 2048, 0.1, 0.9, 0.08),
            ('C', 'D', 1024, 0.2, 0.8, 0.15)
        ]
        
        for a, b, bw, lat, rel, risk in links_data:
            self.world.create_entity(
                NetworkLink(a=a, b=b, bandwidth=bw, latency=lat, 
                           reliability=rel, base_risk=risk)
            )
    
    def _create_factions(self):
        """Create test factions."""
        self.world.create_entity(
            Faction(faction_id='Market', reputation=0, resources=100)
        )
        self.world.create_entity(
            Faction(faction_id='Militia', reputation=0, resources=80)
        )
    
    def _on_delivered(self, **kwargs):
        self.delivered_messages.append(kwargs)
    
    def _on_intercepted(self, **kwargs):
        self.intercepted_messages.append(kwargs)
    
    def test_send_single_message(self):
        """Test sending a single message through the network."""
        # Update systems to build graph
        self.network_system.process(0)
        self.routing_system.process(0)
        
        # Create a message
        message_entity = self.world.create_entity(
            Message(
                msg_id='TEST001',
                origin='A',
                dest='D',
                tag='trade',
                priority=5,
                size=1024,
                reward=20,
                content_snippet='Test message'
            )
        )
        
        # Find route
        route = self.routing_system.find_route('A', 'D')
        assert route is not None
        
        # Spawn signal
        signal_entity = self.signal_system.spawn_signal(message_entity, route.path)
        assert signal_entity is not None
        
        signal = self.world.get_component(signal_entity, Signal)
        assert signal.path == route.path
        assert signal.state == 'traveling'
    
    def test_routing_finds_multiple_paths(self):
        """Test that routing finds multiple alternative paths."""
        self.network_system.process(0)
        self.routing_system.process(0)
        
        routes = self.routing_system.find_alternative_routes('A', 'D', k=3)
        
        assert len(routes) >= 1
        
        # All routes should connect A to D
        for route in routes:
            assert route.path[0] == 'A'
            assert route.path[-1] == 'D'
    
    def test_route_metrics_are_calculated(self):
        """Test that route metrics are properly calculated."""
        self.network_system.process(0)
        self.routing_system.process(0)
        
        route = self.routing_system.find_route('A', 'D')
        
        assert route is not None
        assert route.total_latency > 0
        assert route.intercept_risk >= 0
        assert route.hop_count >= 1
    
    def test_route_cost_calculation(self):
        """Test route cost calculation with encryption."""
        self.network_system.process(0)
        self.routing_system.process(0)
        
        route = self.routing_system.find_route('A', 'D')
        
        # Calculate cost without encryption
        cost_no_enc = self.routing_system.get_route_cost(route.path, encryption_level=0)
        
        # Calculate cost with encryption
        cost_enc = self.routing_system.get_route_cost(route.path, encryption_level=2)
        
        assert cost_enc['encryption_cost'] > cost_no_enc['encryption_cost']
        assert cost_enc['intercept_risk'] < cost_no_enc['intercept_risk']
    
    def test_network_connectivity(self):
        """Test network connectivity checks."""
        self.network_system.process(0)
        
        # All nodes should be connected
        assert self.network_system.get_path_exists('A', 'D')
        assert self.network_system.get_path_exists('A', 'C')
        
        # Neighbors should be correct
        neighbors_a = self.network_system.get_neighbors('A')
        assert 'B' in neighbors_a
    
    def test_link_sabotage(self):
        """Test link sabotage functionality."""
        self.network_system.process(0)
        
        # Sabotage a link
        result = self.network_system.sabotage_link('A', 'B')
        assert result == True
        
        # Link should be inactive
        link = self.network_system.get_link('A', 'B')
        assert link.active == False
        
        # Repair the link
        result = self.network_system.repair_link('A', 'B')
        assert result == True
        assert link.active == True


class TestWorldStateScenario:
    """Integration tests for world state changes."""
    
    def setup_method(self):
        """Set up test world."""
        self.world = World()
        
        # Create nodes
        self.world.create_entity(
            Position(x=100, y=100),
            NetworkNode(node_id='A', trust=0.5, capacity=4096)
        )
        
        self.network_system = NetworkSystem()
        self.network_system.world = self.world
    
    def test_trust_modification(self):
        """Test node trust modification."""
        self.network_system.process(0)
        
        node = self.network_system.get_node('A')
        original_trust = node.trust
        
        # Increase trust
        self.network_system.modify_trust('A', 0.2)
        assert node.trust == original_trust + 0.2
        
        # Trust should be clamped
        self.network_system.modify_trust('A', 0.5)
        assert node.trust <= 1.0
    
    def test_ownership_change(self):
        """Test node ownership changes."""
        self.network_system.process(0)
        
        node = self.network_system.get_node('A')
        assert node.owner is None
        
        # Change owner
        self.network_system.change_node_owner('A', 'TestFaction')
        assert node.owner == 'TestFaction'
        
        # Clear owner
        self.network_system.change_node_owner('A', None)
        assert node.owner is None
    
    def test_bribe_increases_trust(self):
        """Test that bribing increases trust."""
        self.network_system.process(0)
        
        node = self.network_system.get_node('A')
        original_trust = node.trust
        
        self.network_system.bribe_node('A', 50)
        assert node.trust > original_trust


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
