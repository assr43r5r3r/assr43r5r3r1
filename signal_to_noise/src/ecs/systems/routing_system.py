"""
Routing System for computing weighted paths.

Implements Dijkstra and Yen's k-shortest paths algorithms
with customizable weight functions.
"""

from typing import Dict, List, Optional, Callable, Any, Tuple
from ..ecs_core import System
from ..components import NetworkNode, NetworkLink
from ...utils.routing import dijkstra, yen_k_shortest_paths, RouteMetrics, build_graph_from_links
from ...settings import get_settings


class RoutingSystem(System):
    """
    System for computing routes through the network.
    
    Features:
    - Weighted shortest path (Dijkstra)
    - K-shortest paths (Yen's algorithm) for alternatives
    - Customizable weight functions
    - Route metrics calculation
    """
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        
        # Cached graph (updated by NetworkSystem)
        self.graph: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Custom weight function
        self._weight_func: Optional[Callable] = None
        
        # Context for weight calculations
        self._context: Dict[str, Any] = {}
        
        # Hostile factions for routing penalties
        self.hostile_owners: List[str] = []
    
    def process(self, dt: float) -> None:
        """Update routing graph from network state."""
        if not self.world:
            return
        
        self._update_graph()
    
    def _update_graph(self) -> None:
        """Rebuild the routing graph from current network state."""
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
            
            # Bidirectional edges
            if link.a in self.graph:
                self.graph[link.a][link.b] = edge_data.copy()
            if link.b in self.graph:
                self.graph[link.b][link.a] = edge_data.copy()
    
    def set_weight_function(self, func: Callable) -> None:
        """Set a custom weight function for routing."""
        self._weight_func = func
    
    def set_context(self, **kwargs) -> None:
        """Set context data for weight calculations."""
        self._context.update(kwargs)
    
    def add_hostile_owner(self, owner: str) -> None:
        """Add a faction to the hostile list for route penalties."""
        if owner not in self.hostile_owners:
            self.hostile_owners.append(owner)
            self._context['hostile_owners'] = self.hostile_owners
    
    def remove_hostile_owner(self, owner: str) -> None:
        """Remove a faction from the hostile list."""
        if owner in self.hostile_owners:
            self.hostile_owners.remove(owner)
            self._context['hostile_owners'] = self.hostile_owners
    
    def find_route(self, start: str, end: str) -> Optional[RouteMetrics]:
        """
        Find the best route between two nodes.
        
        Args:
            start: Starting node ID
            end: Destination node ID
            
        Returns:
            RouteMetrics with path and metrics, or None if no path exists
        """
        return dijkstra(self.graph, start, end, self._weight_func, self._context)
    
    def find_alternative_routes(self, start: str, end: str, k: int = 3) -> List[RouteMetrics]:
        """
        Find k alternative routes between two nodes.
        
        Args:
            start: Starting node ID
            end: Destination node ID
            k: Number of routes to find (default 3)
            
        Returns:
            List of RouteMetrics, sorted by weight
        """
        return yen_k_shortest_paths(self.graph, start, end, k, self._weight_func, self._context)
    
    def calculate_intercept_risk(self, path: List[str], encryption_level: int = 0) -> float:
        """
        Calculate total interception risk for a path.
        
        P_intercept = 1 - product(1 - edge_risk * (1 - reliability) * f(encryption))
        
        Args:
            path: List of node IDs in the path
            encryption_level: Encryption level (0-3)
            
        Returns:
            Total interception probability (0.0 - 1.0)
        """
        if len(path) < 2:
            return 0.0
        
        # Encryption reduces risk
        encryption_factor = 1.0 - (encryption_level * 0.25)
        
        survival_prob = 1.0
        
        for i in range(len(path) - 1):
            src, dst = path[i], path[i + 1]
            
            if src not in self.graph or dst not in self.graph[src]:
                continue
            
            edge = self.graph[src][dst]
            base_risk = edge.get('base_risk', 0.1)
            reliability = edge.get('reliability', 0.9)
            
            # Edge interception probability
            edge_intercept = base_risk * (1 - reliability) * encryption_factor
            
            # Survival probability for this edge
            survival_prob *= (1 - edge_intercept)
        
        return 1.0 - survival_prob
    
    def calculate_total_latency(self, path: List[str]) -> float:
        """
        Calculate total latency for a path.
        
        Args:
            path: List of node IDs
            
        Returns:
            Total latency in seconds
        """
        if len(path) < 2:
            return 0.0
        
        total = 0.0
        
        for i in range(len(path) - 1):
            src, dst = path[i], path[i + 1]
            
            if src not in self.graph or dst not in self.graph[src]:
                continue
            
            edge = self.graph[src][dst]
            total += edge.get('latency', 0.1)
            
            # Add congestion delay
            load_ratio = edge.get('current_load', 0) / max(edge.get('bandwidth', 1), 1)
            total += edge.get('latency', 0.1) * load_ratio * 0.5
        
        return total
    
    def calculate_min_bandwidth(self, path: List[str]) -> int:
        """
        Calculate the minimum bandwidth along a path (bottleneck).
        
        Args:
            path: List of node IDs
            
        Returns:
            Minimum bandwidth in bytes/second
        """
        if len(path) < 2:
            return 0
        
        min_bw = float('inf')
        
        for i in range(len(path) - 1):
            src, dst = path[i], path[i + 1]
            
            if src not in self.graph or dst not in self.graph[src]:
                return 0
            
            edge = self.graph[src][dst]
            bw = edge.get('bandwidth', 0) - edge.get('current_load', 0)
            min_bw = min(min_bw, max(0, bw))
        
        return int(min_bw) if min_bw != float('inf') else 0
    
    def get_route_cost(self, path: List[str], 
                       encryption_level: int = 0,
                       bribe_nodes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate complete costs and metrics for a route.
        
        Args:
            path: List of node IDs
            encryption_level: Encryption level to apply
            bribe_nodes: Nodes to bribe for trust increase
            
        Returns:
            Dictionary with all route metrics and costs
        """
        bribe_nodes = bribe_nodes or []
        
        base_latency = self.calculate_total_latency(path)
        intercept_risk = self.calculate_intercept_risk(path, encryption_level)
        min_bandwidth = self.calculate_min_bandwidth(path)
        
        # Calculate costs
        encryption_cost = encryption_level * self.settings.ENCRYPTION_COST
        bribe_cost = len(bribe_nodes) * self.settings.BRIBE_COST
        total_cost = encryption_cost + bribe_cost
        
        # Encryption adds latency (size increase)
        encryption_latency = encryption_level * 0.05
        total_latency = base_latency + encryption_latency
        
        return {
            'path': path,
            'hop_count': len(path) - 1,
            'base_latency': base_latency,
            'total_latency': total_latency,
            'intercept_risk': intercept_risk,
            'min_bandwidth': min_bandwidth,
            'encryption_level': encryption_level,
            'encryption_cost': encryption_cost,
            'bribe_cost': bribe_cost,
            'total_cost': total_cost,
            'bribe_nodes': bribe_nodes
        }
