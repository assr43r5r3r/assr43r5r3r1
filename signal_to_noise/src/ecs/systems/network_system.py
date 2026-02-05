"""
Network System for maintaining node and link states.

Handles network topology changes, sabotage, and ownership modifications.
"""

from typing import Dict, Optional, List, Any, Tuple
from ..ecs_core import System, Entity
from ..components import Position, NetworkNode, NetworkLink
from ...settings import get_settings


class NetworkSystem(System):
    """
    System for managing network topology and state.
    
    Features:
    - Node and link state management
    - Sabotage and repair mechanics
    - Ownership changes
    - Network statistics
    """
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        
        # Node and link entity lookups
        self._node_entities: Dict[str, Entity] = {}
        self._link_entities: Dict[Tuple[str, str], Entity] = {}
        
        # Adjacency graph for pathfinding
        self.graph: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Network statistics
        self.stats = {
            'total_nodes': 0,
            'active_nodes': 0,
            'total_links': 0,
            'active_links': 0,
            'compromised_nodes': 0
        }
    
    def process(self, dt: float) -> None:
        """Update network state."""
        if not self.world:
            return
        
        self._update_indexes()
        self._update_graph()
        self._update_stats()
    
    def _update_indexes(self) -> None:
        """Update entity lookup dictionaries."""
        self._node_entities.clear()
        self._link_entities.clear()
        
        for entity, node in self.world.query_with_components(NetworkNode):
            self._node_entities[node.node_id] = entity
        
        for entity, link in self.world.query_with_components(NetworkLink):
            # Store both directions for easy lookup
            self._link_entities[(link.a, link.b)] = entity
            self._link_entities[(link.b, link.a)] = entity
    
    def _update_graph(self) -> None:
        """Update the adjacency graph for pathfinding."""
        self.graph.clear()
        
        # Initialize nodes
        for entity, node in self.world.query_with_components(NetworkNode):
            self.graph[node.node_id] = {}
        
        # Add links as edges
        for entity, link in self.world.query_with_components(NetworkLink):
            if not link.active:
                continue
            
            edge_data = {
                'bandwidth': link.bandwidth,
                'latency': link.latency,
                'reliability': link.reliability,
                'base_risk': link.base_risk,
                'current_load': link.current_load
            }
            
            # Bidirectional
            if link.a in self.graph:
                self.graph[link.a][link.b] = edge_data.copy()
            if link.b in self.graph:
                self.graph[link.b][link.a] = edge_data.copy()
    
    def _update_stats(self) -> None:
        """Update network statistics."""
        self.stats['total_nodes'] = 0
        self.stats['active_nodes'] = 0
        self.stats['compromised_nodes'] = 0
        
        for entity, node in self.world.query_with_components(NetworkNode):
            self.stats['total_nodes'] += 1
            self.stats['active_nodes'] += 1
            if node.trust < 0.3:
                self.stats['compromised_nodes'] += 1
        
        self.stats['total_links'] = 0
        self.stats['active_links'] = 0
        
        for entity, link in self.world.query_with_components(NetworkLink):
            self.stats['total_links'] += 1
            if link.active:
                self.stats['active_links'] += 1
    
    def get_node_entity(self, node_id: str) -> Optional[Entity]:
        """Get the entity for a node by ID."""
        return self._node_entities.get(node_id)
    
    def get_node(self, node_id: str) -> Optional[NetworkNode]:
        """Get the NetworkNode component for a node."""
        entity = self.get_node_entity(node_id)
        if entity and self.world:
            return self.world.get_component(entity, NetworkNode)
        return None
    
    def get_link_entity(self, node_a: str, node_b: str) -> Optional[Entity]:
        """Get the entity for a link between two nodes."""
        return self._link_entities.get((node_a, node_b))
    
    def get_link(self, node_a: str, node_b: str) -> Optional[NetworkLink]:
        """Get the NetworkLink component between two nodes."""
        entity = self.get_link_entity(node_a, node_b)
        if entity and self.world:
            return self.world.get_component(entity, NetworkLink)
        return None
    
    def sabotage_link(self, node_a: str, node_b: str) -> bool:
        """Disable a link between two nodes."""
        link = self.get_link(node_a, node_b)
        if link:
            link.active = False
            if self.world:
                self.world.emit_event('link_sabotaged', a=node_a, b=node_b)
            return True
        return False
    
    def repair_link(self, node_a: str, node_b: str) -> bool:
        """Re-enable a disabled link."""
        link = self.get_link(node_a, node_b)
        if link:
            link.active = True
            if self.world:
                self.world.emit_event('link_repaired', a=node_a, b=node_b)
            return True
        return False
    
    def change_node_owner(self, node_id: str, new_owner: Optional[str]) -> bool:
        """Change the owner of a node."""
        node = self.get_node(node_id)
        if node:
            old_owner = node.owner
            node.owner = new_owner
            if self.world:
                self.world.emit_event('node_ownership_changed', 
                                     node_id=node_id, 
                                     old_owner=old_owner, 
                                     new_owner=new_owner)
            return True
        return False
    
    def modify_trust(self, node_id: str, delta: float) -> bool:
        """Modify the trust level of a node."""
        node = self.get_node(node_id)
        if node:
            old_trust = node.trust
            node.trust = max(0.0, min(1.0, node.trust + delta))
            if self.world:
                self.world.emit_event('node_trust_changed',
                                     node_id=node_id,
                                     old_trust=old_trust,
                                     new_trust=node.trust)
            return True
        return False
    
    def bribe_node(self, node_id: str, amount: int) -> bool:
        """
        Attempt to bribe a node for temporary trust increase.
        
        Args:
            node_id: Node to bribe
            amount: Bribe amount (affects trust increase)
            
        Returns:
            True if bribe successful
        """
        node = self.get_node(node_id)
        if node:
            # Trust increase based on bribe amount
            trust_increase = min(0.3, amount / 100.0)
            self.modify_trust(node_id, trust_increase)
            
            if self.world:
                self.world.emit_event('node_bribed',
                                     node_id=node_id,
                                     amount=amount,
                                     trust_increase=trust_increase)
            return True
        return False
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all neighboring node IDs."""
        if node_id in self.graph:
            return list(self.graph[node_id].keys())
        return []
    
    def get_path_exists(self, start: str, end: str) -> bool:
        """Check if a path exists between two nodes."""
        if start not in self.graph or end not in self.graph:
            return False
        
        # BFS to check connectivity
        visited = set()
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            if current == end:
                return True
            
            if current in visited:
                continue
            visited.add(current)
            
            for neighbor in self.graph.get(current, {}):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        return False
    
    def get_all_nodes(self) -> List[str]:
        """Get list of all node IDs."""
        return list(self._node_entities.keys())
    
    def get_nodes_by_owner(self, owner: Optional[str]) -> List[str]:
        """Get all nodes owned by a specific faction."""
        result = []
        for entity, node in self.world.query_with_components(NetworkNode):
            if node.owner == owner:
                result.append(node.node_id)
        return result
