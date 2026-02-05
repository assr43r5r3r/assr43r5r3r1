"""
Unit tests for routing algorithms (Dijkstra and Yen's k-shortest paths).
"""

import pytest
import sys
import os

# Add the signal_to_noise directory to path
signal_to_noise_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, signal_to_noise_dir)

from src.utils.routing import (
    dijkstra, yen_k_shortest_paths, build_graph_from_links,
    default_weight_function, RouteMetrics
)


class TestDijkstra:
    """Tests for Dijkstra's algorithm."""
    
    def create_simple_graph(self):
        """Create a simple test graph."""
        return {
            'A': {
                'B': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0},
                'C': {'latency': 0.2, 'base_risk': 0.2, 'reliability': 0.8, 'bandwidth': 1024, 'current_load': 0}
            },
            'B': {
                'A': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0},
                'C': {'latency': 0.05, 'base_risk': 0.05, 'reliability': 0.95, 'bandwidth': 3072, 'current_load': 0},
                'D': {'latency': 0.15, 'base_risk': 0.15, 'reliability': 0.85, 'bandwidth': 1536, 'current_load': 0}
            },
            'C': {
                'A': {'latency': 0.2, 'base_risk': 0.2, 'reliability': 0.8, 'bandwidth': 1024, 'current_load': 0},
                'B': {'latency': 0.05, 'base_risk': 0.05, 'reliability': 0.95, 'bandwidth': 3072, 'current_load': 0},
                'D': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0}
            },
            'D': {
                'B': {'latency': 0.15, 'base_risk': 0.15, 'reliability': 0.85, 'bandwidth': 1536, 'current_load': 0},
                'C': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0}
            }
        }
    
    def test_dijkstra_finds_path(self):
        """Test that Dijkstra finds a path between connected nodes."""
        graph = self.create_simple_graph()
        result = dijkstra(graph, 'A', 'D')
        
        assert result is not None
        assert result.path[0] == 'A'
        assert result.path[-1] == 'D'
        assert len(result.path) >= 2
    
    def test_dijkstra_optimal_path(self):
        """Test that Dijkstra finds the optimal path."""
        graph = self.create_simple_graph()
        result = dijkstra(graph, 'A', 'D')
        
        # The path through B and C should be optimal
        assert result is not None
        assert len(result.path) <= 4  # At most A -> B -> C -> D
    
    def test_dijkstra_no_path(self):
        """Test that Dijkstra returns None when no path exists."""
        graph = {
            'A': {'B': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0}},
            'B': {'A': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0}},
            'C': {}  # Disconnected node
        }
        
        result = dijkstra(graph, 'A', 'C')
        assert result is None
    
    def test_dijkstra_same_start_end(self):
        """Test Dijkstra with same start and end node."""
        graph = self.create_simple_graph()
        result = dijkstra(graph, 'A', 'A')
        
        assert result is not None
        assert result.path == ['A']
        assert result.hop_count == 0
    
    def test_dijkstra_direct_connection(self):
        """Test Dijkstra with directly connected nodes."""
        graph = self.create_simple_graph()
        result = dijkstra(graph, 'A', 'B')
        
        assert result is not None
        assert result.path == ['A', 'B']
        assert result.hop_count == 1
    
    def test_dijkstra_unknown_node(self):
        """Test Dijkstra with unknown start or end node."""
        graph = self.create_simple_graph()
        
        assert dijkstra(graph, 'X', 'D') is None
        assert dijkstra(graph, 'A', 'X') is None
    
    def test_dijkstra_metrics(self):
        """Test that Dijkstra returns correct metrics."""
        graph = self.create_simple_graph()
        result = dijkstra(graph, 'A', 'B')
        
        assert result is not None
        assert result.total_latency >= 0
        assert result.intercept_risk >= 0
        assert result.intercept_risk <= 1.0
        assert result.total_weight >= 0


class TestYenKShortestPaths:
    """Tests for Yen's k-shortest paths algorithm."""
    
    def create_graph_with_alternatives(self):
        """Create a graph with multiple paths."""
        return {
            'A': {
                'B': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0},
                'C': {'latency': 0.15, 'base_risk': 0.15, 'reliability': 0.85, 'bandwidth': 1536, 'current_load': 0}
            },
            'B': {
                'A': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0},
                'D': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0}
            },
            'C': {
                'A': {'latency': 0.15, 'base_risk': 0.15, 'reliability': 0.85, 'bandwidth': 1536, 'current_load': 0},
                'D': {'latency': 0.2, 'base_risk': 0.2, 'reliability': 0.8, 'bandwidth': 1024, 'current_load': 0}
            },
            'D': {
                'B': {'latency': 0.1, 'base_risk': 0.1, 'reliability': 0.9, 'bandwidth': 2048, 'current_load': 0},
                'C': {'latency': 0.2, 'base_risk': 0.2, 'reliability': 0.8, 'bandwidth': 1024, 'current_load': 0}
            }
        }
    
    def test_yen_finds_multiple_paths(self):
        """Test that Yen's algorithm finds multiple paths."""
        graph = self.create_graph_with_alternatives()
        results = yen_k_shortest_paths(graph, 'A', 'D', k=3)
        
        assert len(results) >= 1
        # All paths should start at A and end at D
        for result in results:
            assert result.path[0] == 'A'
            assert result.path[-1] == 'D'
    
    def test_yen_paths_are_sorted(self):
        """Test that paths are sorted by weight."""
        graph = self.create_graph_with_alternatives()
        results = yen_k_shortest_paths(graph, 'A', 'D', k=3)
        
        if len(results) >= 2:
            for i in range(len(results) - 1):
                assert results[i].total_weight <= results[i + 1].total_weight
    
    def test_yen_paths_are_unique(self):
        """Test that all returned paths are unique."""
        graph = self.create_graph_with_alternatives()
        results = yen_k_shortest_paths(graph, 'A', 'D', k=5)
        
        paths = [tuple(r.path) for r in results]
        assert len(paths) == len(set(paths))  # All unique
    
    def test_yen_respects_k_limit(self):
        """Test that Yen's algorithm respects the k limit."""
        graph = self.create_graph_with_alternatives()
        results = yen_k_shortest_paths(graph, 'A', 'D', k=2)
        
        assert len(results) <= 2
    
    def test_yen_no_path(self):
        """Test Yen's algorithm when no path exists."""
        graph = {
            'A': {},
            'B': {}
        }
        
        results = yen_k_shortest_paths(graph, 'A', 'B', k=3)
        assert len(results) == 0


class TestBuildGraph:
    """Tests for graph building from node/link data."""
    
    def test_build_graph_basic(self):
        """Test basic graph construction."""
        nodes = [
            {'id': 'A'},
            {'id': 'B'},
            {'id': 'C'}
        ]
        links = [
            {'a': 'A', 'b': 'B', 'bandwidth': 2048, 'latency': 0.1, 'reliability': 0.9, 'base_risk': 0.1},
            {'a': 'B', 'b': 'C', 'bandwidth': 1024, 'latency': 0.2, 'reliability': 0.8, 'base_risk': 0.2}
        ]
        
        graph = build_graph_from_links(nodes, links)
        
        assert 'A' in graph
        assert 'B' in graph
        assert 'C' in graph
        assert 'B' in graph['A']
        assert 'A' in graph['B']  # Bidirectional
        assert 'C' in graph['B']
        assert 'B' in graph['C']
    
    def test_build_graph_edge_properties(self):
        """Test that edge properties are correctly set."""
        nodes = [{'id': 'A'}, {'id': 'B'}]
        links = [
            {'a': 'A', 'b': 'B', 'bandwidth': 2048, 'latency': 0.1, 'reliability': 0.9, 'base_risk': 0.1}
        ]
        
        graph = build_graph_from_links(nodes, links)
        
        edge = graph['A']['B']
        assert edge['bandwidth'] == 2048
        assert edge['latency'] == 0.1
        assert edge['reliability'] == 0.9
        assert edge['base_risk'] == 0.1


class TestWeightFunction:
    """Tests for the weight function."""
    
    def test_default_weight_positive(self):
        """Test that default weight is always positive."""
        edge = {
            'latency': 0.1,
            'base_risk': 0.1,
            'reliability': 0.9,
            'bandwidth': 2048,
            'current_load': 0
        }
        
        weight = default_weight_function(edge, 'A', 'B', None)
        assert weight > 0
    
    def test_weight_increases_with_risk(self):
        """Test that weight increases with higher risk."""
        low_risk_edge = {
            'latency': 0.1,
            'base_risk': 0.1,
            'reliability': 0.9,
            'bandwidth': 2048,
            'current_load': 0
        }
        
        high_risk_edge = {
            'latency': 0.1,
            'base_risk': 0.5,
            'reliability': 0.5,
            'bandwidth': 2048,
            'current_load': 0
        }
        
        low_weight = default_weight_function(low_risk_edge, 'A', 'B', None)
        high_weight = default_weight_function(high_risk_edge, 'A', 'B', None)
        
        assert high_weight > low_weight
    
    def test_weight_increases_with_load(self):
        """Test that weight increases with higher load."""
        low_load_edge = {
            'latency': 0.1,
            'base_risk': 0.1,
            'reliability': 0.9,
            'bandwidth': 2048,
            'current_load': 0
        }
        
        high_load_edge = {
            'latency': 0.1,
            'base_risk': 0.1,
            'reliability': 0.9,
            'bandwidth': 2048,
            'current_load': 1500
        }
        
        low_weight = default_weight_function(low_load_edge, 'A', 'B', None)
        high_weight = default_weight_function(high_load_edge, 'A', 'B', None)
        
        assert high_weight > low_weight


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
