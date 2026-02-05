"""
AI System for faction agents and interceptors.

Implements simple AI behaviors for enemy factions and interceptors.
"""

import random
from typing import Dict, List, Optional, Any
from ..ecs_core import System, Entity
from ..components import (
    Interceptor, NetworkNode, NetworkLink, Signal, 
    Faction, Position, Timer
)
from ...settings import get_settings


class AISystem(System):
    """
    System for AI-controlled entities.
    
    Features:
    - Interceptor patrol behavior
    - Faction resource management
    - Strategic goal-oriented actions
    """
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        
        # AI update rate (slower than game tick for performance)
        self._update_interval: float = 1.0  # seconds
        self._update_timer: float = 0.0
        
        # Faction goals
        self.faction_goals: Dict[str, List[str]] = {}
        
        # Statistics
        self.stats = {
            'interceptors_active': 0,
            'captures_attempted': 0,
            'captures_successful': 0
        }
    
    def process(self, dt: float) -> None:
        """Process AI behaviors."""
        if not self.world:
            return
        
        self._update_timer += dt
        
        if self._update_timer >= self._update_interval:
            self._update_timer = 0.0
            self._update_interceptors()
            self._update_factions()
    
    def _update_interceptors(self) -> None:
        """Update all interceptor behaviors."""
        active_count = 0
        
        for entity, interceptor in self.world.query_with_components(Interceptor):
            if not interceptor.active:
                continue
            
            active_count += 1
            
            # Patrol behavior
            self._patrol_interceptor(entity, interceptor)
            
            # Try to capture signals
            self._attempt_captures(entity, interceptor)
        
        self.stats['interceptors_active'] = active_count
    
    def _patrol_interceptor(self, entity: Entity, interceptor: Interceptor) -> None:
        """Move interceptor to next patrol node."""
        if not interceptor.patrol_nodes:
            return
        
        # Find current position in patrol
        if interceptor.current_node not in interceptor.patrol_nodes:
            interceptor.current_node = interceptor.patrol_nodes[0]
            return
        
        # Move to next node with some randomness
        current_idx = interceptor.patrol_nodes.index(interceptor.current_node)
        
        if random.random() < 0.3:
            # Random jump
            interceptor.current_node = random.choice(interceptor.patrol_nodes)
        else:
            # Sequential patrol
            next_idx = (current_idx + 1) % len(interceptor.patrol_nodes)
            interceptor.current_node = interceptor.patrol_nodes[next_idx]
    
    def _attempt_captures(self, entity: Entity, interceptor: Interceptor) -> None:
        """Attempt to capture signals near the interceptor."""
        if not interceptor.current_node:
            return
        
        # Find nearby signals
        nearby_signals = self._get_signals_near_node(
            interceptor.current_node, 
            interceptor.detection_range
        )
        
        for signal_entity, signal in nearby_signals:
            self.stats['captures_attempted'] += 1
            
            # Calculate capture probability
            capture_prob = interceptor.capture_skill
            
            # Encrypted signals are harder to capture
            if signal.encrypted:
                capture_prob *= 0.5
            
            # Attempt capture
            if random.random() < capture_prob:
                signal.state = 'intercepted'
                self.stats['captures_successful'] += 1
                
                if self.world:
                    self.world.emit_event('signal_captured',
                                         signal_id=signal_entity.id,
                                         interceptor=interceptor.interceptor_id,
                                         location=interceptor.current_node)
    
    def _get_signals_near_node(self, node_id: str, 
                               range_hops: int) -> List[tuple]:
        """Get signals within range of a node."""
        nearby = []
        
        # Get nodes within range
        nearby_nodes = self._get_nodes_within_range(node_id, range_hops)
        
        for entity, signal in self.world.query_with_components(Signal):
            if signal.state not in ('traveling', 'queued'):
                continue
            
            # Check if signal is at a nearby node
            if signal.current_index < len(signal.path):
                current_node = signal.path[signal.current_index]
                if current_node in nearby_nodes:
                    nearby.append((entity, signal))
        
        return nearby
    
    def _get_nodes_within_range(self, start: str, range_hops: int) -> set:
        """Get all nodes within a certain number of hops."""
        if range_hops < 0:
            return set()
        
        visited = {start}
        frontier = [start]
        
        for _ in range(range_hops):
            next_frontier = []
            for node in frontier:
                neighbors = self._get_neighbors(node)
                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.append(neighbor)
            frontier = next_frontier
        
        return visited
    
    def _get_neighbors(self, node_id: str) -> List[str]:
        """Get neighboring nodes."""
        neighbors = []
        
        for entity, link in self.world.query_with_components(NetworkLink):
            if not link.active:
                continue
            
            if link.a == node_id:
                neighbors.append(link.b)
            elif link.b == node_id:
                neighbors.append(link.a)
        
        return neighbors
    
    def _update_factions(self) -> None:
        """Update faction behaviors."""
        for entity, faction in self.world.query_with_components(Faction):
            self._update_faction(entity, faction)
    
    def _update_faction(self, entity: Entity, faction: Faction) -> None:
        """Update a single faction's behavior."""
        # Simple resource regeneration
        if faction.resources < 100:
            faction.resources += 1
        
        # Check for strategic actions based on goals
        goals = self.faction_goals.get(faction.faction_id, [])
        
        for goal in goals:
            if goal == 'expand' and faction.resources > 50:
                # Try to claim a neutral node
                self._faction_try_expand(faction)
            elif goal == 'defend':
                # Strengthen owned nodes
                self._faction_strengthen_nodes(faction)
    
    def _faction_try_expand(self, faction: Faction) -> None:
        """Try to expand faction territory."""
        # Find neutral nodes adjacent to owned nodes
        owned_nodes = self._get_faction_nodes(faction.faction_id)
        
        for node_id in owned_nodes:
            neighbors = self._get_neighbors(node_id)
            for neighbor in neighbors:
                node = self._get_node(neighbor)
                if node and node.owner is None:
                    # Try to claim
                    if faction.resources >= 30:
                        node.owner = faction.faction_id
                        faction.resources -= 30
                        return
    
    def _faction_strengthen_nodes(self, faction: Faction) -> None:
        """Strengthen faction-owned nodes."""
        owned_nodes = self._get_faction_nodes(faction.faction_id)
        
        for node_id in owned_nodes:
            node = self._get_node(node_id)
            if node and node.trust < 0.8 and faction.resources >= 10:
                node.trust = min(1.0, node.trust + 0.1)
                faction.resources -= 10
    
    def _get_faction_nodes(self, faction_id: str) -> List[str]:
        """Get all nodes owned by a faction."""
        nodes = []
        for entity, node in self.world.query_with_components(NetworkNode):
            if node.owner == faction_id:
                nodes.append(node.node_id)
        return nodes
    
    def _get_node(self, node_id: str) -> Optional[NetworkNode]:
        """Get node by ID."""
        for entity, node in self.world.query_with_components(NetworkNode):
            if node.node_id == node_id:
                return node
        return None
    
    def spawn_interceptor(self, interceptor_id: str,
                         owner: str,
                         patrol_nodes: List[str],
                         skill: float = 0.5) -> Entity:
        """
        Create a new interceptor entity.
        
        Args:
            interceptor_id: Unique identifier
            owner: Owning faction ID
            patrol_nodes: List of nodes to patrol
            skill: Capture skill level (0.0 - 1.0)
            
        Returns:
            Created interceptor entity
        """
        start_node = patrol_nodes[0] if patrol_nodes else ""
        
        return self.world.create_entity(
            Interceptor(
                interceptor_id=interceptor_id,
                owner=owner,
                patrol_nodes=patrol_nodes,
                current_node=start_node,
                capture_skill=skill,
                active=True
            )
        )
    
    def set_faction_goal(self, faction_id: str, goals: List[str]) -> None:
        """Set strategic goals for a faction."""
        self.faction_goals[faction_id] = goals
