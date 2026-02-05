"""
Routing algorithms for network pathfinding.

Implements:
- Weighted Dijkstra's algorithm for shortest path
- Yen's K-shortest paths algorithm for alternative routes

These algorithms support custom weight functions for flexible routing strategies.
"""

import heapq
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class RouteMetrics:
    """Metrics for a computed route."""
    path: List[str]
    total_weight: float
    total_latency: float
    intercept_risk: float
    bandwidth_usage: float
    hop_count: int
    
    def __repr__(self) -> str:
        return (f"Route({' -> '.join(self.path)}, "
                f"weight={self.total_weight:.2f}, "
                f"latency={self.total_latency:.2f}s, "
                f"risk={self.intercept_risk:.2%})")


def default_weight_function(edge: Dict[str, Any], 
                            source: str, 
                            target: str,
                            context: Optional[Dict] = None) -> float:
    """
    Default weight function for routing.
    
    Weight = latency + penalty(interception_risk, bandwidth_usage, owner_penalty)
    
    Args:
        edge: Edge data dictionary with bandwidth, latency, reliability, base_risk
        source: Source node ID
        target: Target node ID
        context: Optional context with additional info (node data, etc.)
        
    Returns:
        Computed edge weight
    """
    latency = edge.get('latency', 0.1)
    base_risk = edge.get('base_risk', 0.1)
    reliability = edge.get('reliability', 0.9)
    bandwidth = edge.get('bandwidth', 2048)
    current_load = edge.get('current_load', 0)
    
    # Base weight is latency
    weight = latency
    
    # Add interception risk penalty
    intercept_penalty = base_risk * (1 - reliability) * 2.0
    weight += intercept_penalty
    
    # Add bandwidth congestion penalty
    if bandwidth > 0:
        load_ratio = current_load / bandwidth
        congestion_penalty = load_ratio * 0.5
        weight += congestion_penalty
    
    # Add owner penalty if context provides it
    if context and 'hostile_owners' in context:
        if edge.get('owner') in context['hostile_owners']:
            weight += 1.0
    
    return max(0.001, weight)  # Ensure positive weight


def dijkstra(graph: Dict[str, Dict[str, Dict[str, Any]]],
             start: str,
             end: str,
             weight_func: Optional[Callable] = None,
             context: Optional[Dict] = None) -> Optional[RouteMetrics]:
    """
    Compute shortest path using Dijkstra's algorithm with custom weights.
    
    Args:
        graph: Adjacency dict {node_id: {neighbor_id: edge_data}}
        start: Starting node ID
        end: Destination node ID
        weight_func: Optional custom weight function (edge, src, dst, ctx) -> float
        context: Optional context dict passed to weight function
        
    Returns:
        RouteMetrics with path and metrics, or None if no path exists
    
    Example:
        >>> graph = {
        ...     'A': {'B': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048}},
        ...     'B': {'A': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048},
        ...           'C': {'latency': 0.2, 'base_risk': 0.2, 'reliability': 0.8, 'bandwidth': 1024}},
        ...     'C': {'B': {'latency': 0.2, 'base_risk': 0.2, 'reliability': 0.8, 'bandwidth': 1024}}
        ... }
        >>> result = dijkstra(graph, 'A', 'C')
        >>> result.path
        ['A', 'B', 'C']
    """
    if start not in graph or end not in graph:
        return None
    
    if weight_func is None:
        weight_func = default_weight_function
    
    # Priority queue: (distance, node, path)
    heap = [(0.0, start, [start])]
    visited = set()
    
    # Track metrics along the path
    distances: Dict[str, float] = {start: 0.0}
    latencies: Dict[str, float] = {start: 0.0}
    risks: Dict[str, float] = {start: 0.0}
    bandwidths: Dict[str, float] = {start: 0.0}
    
    while heap:
        current_dist, current_node, path = heapq.heappop(heap)
        
        if current_node in visited:
            continue
        visited.add(current_node)
        
        if current_node == end:
            # Compute aggregate metrics
            total_latency = latencies.get(current_node, 0.0)
            # Combine risks: P(any intercept) = 1 - product(1 - risk_i)
            total_risk = risks.get(current_node, 0.0)
            avg_bandwidth = bandwidths.get(current_node, 0.0) / max(1, len(path) - 1)
            
            return RouteMetrics(
                path=path,
                total_weight=current_dist,
                total_latency=total_latency,
                intercept_risk=min(1.0, total_risk),
                bandwidth_usage=avg_bandwidth,
                hop_count=len(path) - 1
            )
        
        if current_node not in graph:
            continue
            
        for neighbor, edge_data in graph[current_node].items():
            if neighbor in visited:
                continue
            
            edge_weight = weight_func(edge_data, current_node, neighbor, context)
            new_dist = current_dist + edge_weight
            
            if neighbor not in distances or new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                
                # Track cumulative metrics
                edge_latency = edge_data.get('latency', 0.1)
                edge_risk = edge_data.get('base_risk', 0.1) * (1 - edge_data.get('reliability', 0.9))
                edge_bandwidth = edge_data.get('current_load', 0)
                
                latencies[neighbor] = latencies.get(current_node, 0.0) + edge_latency
                # Accumulate risk (simplified additive model)
                risks[neighbor] = risks.get(current_node, 0.0) + edge_risk
                bandwidths[neighbor] = bandwidths.get(current_node, 0.0) + edge_bandwidth
                
                new_path = path + [neighbor]
                heapq.heappush(heap, (new_dist, neighbor, new_path))
    
    return None  # No path found


def yen_k_shortest_paths(graph: Dict[str, Dict[str, Dict[str, Any]]],
                         start: str,
                         end: str,
                         k: int = 3,
                         weight_func: Optional[Callable] = None,
                         context: Optional[Dict] = None) -> List[RouteMetrics]:
    """
    Compute K shortest paths using Yen's algorithm.
    
    Yen's algorithm finds the k shortest loopless paths between two nodes.
    It uses Dijkstra as a subroutine and iteratively finds deviations from
    the shortest path.
    
    Args:
        graph: Adjacency dict {node_id: {neighbor_id: edge_data}}
        start: Starting node ID
        end: Destination node ID
        k: Number of paths to find (default 3)
        weight_func: Optional custom weight function
        context: Optional context dict for weight function
        
    Returns:
        List of RouteMetrics, up to k paths, sorted by weight
        
    Example:
        >>> graph = create_test_graph()
        >>> paths = yen_k_shortest_paths(graph, 'A', 'D', k=3)
        >>> len(paths) <= 3
        True
    """
    if weight_func is None:
        weight_func = default_weight_function
    
    # Find the shortest path first
    shortest = dijkstra(graph, start, end, weight_func, context)
    if shortest is None:
        return []
    
    # A will store the k shortest paths
    A: List[RouteMetrics] = [shortest]
    
    # B is a heap of potential paths
    B: List[Tuple[float, List[str]]] = []
    
    for i in range(1, k):
        # Get the previous shortest path
        prev_path = A[i - 1].path
        
        for j in range(len(prev_path) - 1):
            # Spur node is the j-th node of the previous path
            spur_node = prev_path[j]
            root_path = prev_path[:j + 1]
            
            # Create modified graph by removing edges
            removed_edges: List[Tuple[str, str, Dict]] = []
            
            # Remove edges that are part of previous shortest paths with same root
            for p in A:
                if len(p.path) > j and p.path[:j + 1] == root_path:
                    # Remove the edge from spur_node to next node in this path
                    if j + 1 < len(p.path):
                        next_node = p.path[j + 1]
                        if spur_node in graph and next_node in graph[spur_node]:
                            edge_data = graph[spur_node].pop(next_node)
                            removed_edges.append((spur_node, next_node, edge_data))
            
            # Remove nodes in root path (except spur node) from graph temporarily
            removed_nodes: Dict[str, Dict] = {}
            for node in root_path[:-1]:
                if node in graph:
                    removed_nodes[node] = graph.pop(node)
                # Also remove incoming edges to this node
                for other_node in list(graph.keys()):
                    if node in graph.get(other_node, {}):
                        if other_node not in removed_edges:
                            edge_data = graph[other_node].pop(node)
                            removed_edges.append((other_node, node, edge_data))
            
            # Calculate spur path from spur node to destination
            spur_path = dijkstra(graph, spur_node, end, weight_func, context)
            
            # Restore removed edges and nodes
            for src, dst, edge_data in removed_edges:
                if src in graph:
                    graph[src][dst] = edge_data
                elif src in removed_nodes:
                    removed_nodes[src][dst] = edge_data
            
            for node, neighbors in removed_nodes.items():
                graph[node] = neighbors
            
            if spur_path is not None:
                # Combine root path with spur path
                total_path = root_path[:-1] + spur_path.path
                
                # Check if this path is already in B
                total_weight = _compute_path_weight(graph, total_path, weight_func, context)
                
                path_tuple = (total_weight, total_path)
                if not _path_in_heap(B, total_path):
                    heapq.heappush(B, path_tuple)
        
        if not B:
            break
        
        # Add the best candidate to A
        while B:
            best_weight, best_path = heapq.heappop(B)
            # Verify path is not duplicate
            if not any(r.path == best_path for r in A):
                metrics = _compute_path_metrics(graph, best_path, weight_func, context)
                if metrics:
                    A.append(metrics)
                    break
    
    return A


def _compute_path_weight(graph: Dict[str, Dict[str, Dict[str, Any]]],
                         path: List[str],
                         weight_func: Callable,
                         context: Optional[Dict]) -> float:
    """Compute total weight for a path."""
    total = 0.0
    for i in range(len(path) - 1):
        src, dst = path[i], path[i + 1]
        if src in graph and dst in graph[src]:
            total += weight_func(graph[src][dst], src, dst, context)
        else:
            return float('inf')
    return total


def _compute_path_metrics(graph: Dict[str, Dict[str, Dict[str, Any]]],
                          path: List[str],
                          weight_func: Callable,
                          context: Optional[Dict]) -> Optional[RouteMetrics]:
    """Compute full metrics for a path."""
    if len(path) < 2:
        return None
    
    total_weight = 0.0
    total_latency = 0.0
    total_risk = 0.0
    total_load = 0.0
    
    for i in range(len(path) - 1):
        src, dst = path[i], path[i + 1]
        if src not in graph or dst not in graph[src]:
            return None
        
        edge = graph[src][dst]
        total_weight += weight_func(edge, src, dst, context)
        total_latency += edge.get('latency', 0.1)
        total_risk += edge.get('base_risk', 0.1) * (1 - edge.get('reliability', 0.9))
        total_load += edge.get('current_load', 0)
    
    return RouteMetrics(
        path=path,
        total_weight=total_weight,
        total_latency=total_latency,
        intercept_risk=min(1.0, total_risk),
        bandwidth_usage=total_load / max(1, len(path) - 1),
        hop_count=len(path) - 1
    )


def _path_in_heap(heap: List[Tuple[float, List[str]]], path: List[str]) -> bool:
    """Check if a path is already in the heap."""
    for _, p in heap:
        if p == path:
            return True
    return False


def build_graph_from_links(nodes: List[Dict], links: List[Dict]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Build an adjacency graph from node and link data.
    
    Args:
        nodes: List of node dicts with 'id' field
        links: List of link dicts with 'a', 'b' and edge properties
        
    Returns:
        Adjacency dict suitable for routing algorithms
    """
    graph: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    # Initialize nodes
    for node in nodes:
        node_id = node.get('id', '')
        if node_id:
            graph[node_id] = {}
    
    # Add bidirectional edges
    for link in links:
        a = link.get('a', '')
        b = link.get('b', '')
        
        if a and b and a in graph and b in graph:
            edge_data = {
                'bandwidth': link.get('bandwidth', 2048),
                'latency': link.get('latency', 0.1),
                'reliability': link.get('reliability', 0.9),
                'base_risk': link.get('base_risk', 0.1),
                'current_load': link.get('current_load', 0)
            }
            # Bidirectional
            graph[a][b] = edge_data.copy()
            graph[b][a] = edge_data.copy()
    
    return graph
