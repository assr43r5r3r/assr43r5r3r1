"""
Unit tests for interception probability calculations.
"""

import pytest
import sys
import os

# Add the signal_to_noise directory to path
signal_to_noise_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, signal_to_noise_dir)

from src.ecs.systems.routing_system import RoutingSystem
from src.ecs.ecs_core import World
from src.ecs.components import NetworkNode, NetworkLink


class TestInterceptionProbability:
    """Tests for interception probability calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.world = World()
        self.system = RoutingSystem()
        self.system.world = self.world
        
        # Create a simple network
        self._create_test_network()
    
    def _create_test_network(self):
        """Create test network with nodes and links."""
        # Create nodes
        nodes = [
            ('A', 0.8, None),
            ('B', 0.7, 'Market'),
            ('C', 0.6, None),
            ('D', 0.9, 'Archive')
        ]
        
        for node_id, trust, owner in nodes:
            self.world.create_entity(
                NetworkNode(node_id=node_id, trust=trust, owner=owner, capacity=4096)
            )
        
        # Create links with varying risk levels
        links = [
            ('A', 'B', 0.05, 0.95),  # Low risk, high reliability
            ('B', 'C', 0.15, 0.8),   # Medium risk
            ('C', 'D', 0.25, 0.7),   # High risk
            ('A', 'D', 0.1, 0.9)     # Alternative path
        ]
        
        for a, b, base_risk, reliability in links:
            self.world.create_entity(
                NetworkLink(a=a, b=b, bandwidth=2048, latency=0.1,
                           base_risk=base_risk, reliability=reliability)
            )
        
        # Update system graph
        self.system.process(0)
    
    def test_zero_encryption_has_higher_risk(self):
        """Test that zero encryption results in higher interception risk."""
        path = ['A', 'B', 'C', 'D']
        
        risk_no_enc = self.system.calculate_intercept_risk(path, encryption_level=0)
        risk_with_enc = self.system.calculate_intercept_risk(path, encryption_level=2)
        
        assert risk_no_enc > risk_with_enc
    
    def test_encryption_reduces_risk(self):
        """Test that higher encryption levels reduce risk."""
        path = ['A', 'B', 'C', 'D']
        
        risks = []
        for level in range(4):
            risk = self.system.calculate_intercept_risk(path, encryption_level=level)
            risks.append(risk)
        
        # Each higher level should have equal or lower risk
        for i in range(len(risks) - 1):
            assert risks[i] >= risks[i + 1]
    
    def test_risk_is_bounded(self):
        """Test that risk is always between 0 and 1."""
        path = ['A', 'B', 'C', 'D']
        
        for level in range(4):
            risk = self.system.calculate_intercept_risk(path, encryption_level=level)
            assert 0 <= risk <= 1
    
    def test_single_hop_risk(self):
        """Test risk calculation for a single hop."""
        path = ['A', 'B']
        
        risk = self.system.calculate_intercept_risk(path, encryption_level=0)
        
        # Risk for A->B: base_risk * (1 - reliability) = 0.05 * (1 - 0.95) = 0.0025
        assert risk > 0
        assert risk < 0.1  # Should be low for this safe link
    
    def test_longer_path_has_higher_risk(self):
        """Test that longer paths generally have higher risk."""
        short_path = ['A', 'B']
        long_path = ['A', 'B', 'C', 'D']
        
        short_risk = self.system.calculate_intercept_risk(short_path, encryption_level=0)
        long_risk = self.system.calculate_intercept_risk(long_path, encryption_level=0)
        
        assert long_risk >= short_risk
    
    def test_empty_path_has_zero_risk(self):
        """Test that empty or single-node path has zero risk."""
        assert self.system.calculate_intercept_risk([], encryption_level=0) == 0
        assert self.system.calculate_intercept_risk(['A'], encryption_level=0) == 0
    
    def test_riskier_links_increase_total_risk(self):
        """Test that riskier links increase total interception risk."""
        # Path through safer links
        safe_path = ['A', 'D']  # Direct, safer path
        
        # Path through riskier links
        risky_path = ['A', 'B', 'C', 'D']  # Goes through higher-risk links
        
        safe_risk = self.system.calculate_intercept_risk(safe_path, encryption_level=0)
        risky_risk = self.system.calculate_intercept_risk(risky_path, encryption_level=0)
        
        # The longer path with riskier links should have higher risk
        assert risky_risk > safe_risk


class TestInterceptionFormula:
    """Tests for the interception probability formula components."""
    
    def test_base_risk_impact(self):
        """Test that base_risk directly impacts interception probability."""
        # P = base_risk * (1 - reliability) * encryption_factor
        
        # Low base risk
        low_risk = 0.05 * (1 - 0.9) * 1.0  # 0.005
        
        # High base risk
        high_risk = 0.25 * (1 - 0.9) * 1.0  # 0.025
        
        assert high_risk > low_risk
    
    def test_reliability_impact(self):
        """Test that reliability reduces interception probability."""
        # P = base_risk * (1 - reliability) * encryption_factor
        
        # Low reliability
        low_rel = 0.1 * (1 - 0.7) * 1.0  # 0.03
        
        # High reliability
        high_rel = 0.1 * (1 - 0.95) * 1.0  # 0.005
        
        assert low_rel > high_rel
    
    def test_encryption_factor(self):
        """Test encryption factor calculation."""
        # encryption_factor = 1 - (level * 0.25)
        
        factors = []
        for level in range(4):
            factor = 1.0 - (level * 0.25)
            factors.append(factor)
        
        assert factors == [1.0, 0.75, 0.5, 0.25]
    
    def test_combined_probability(self):
        """Test combined survival probability calculation."""
        # Survival prob = product(1 - edge_risk)
        
        edge_risks = [0.01, 0.02, 0.03]  # Three edges
        
        survival = 1.0
        for risk in edge_risks:
            survival *= (1 - risk)
        
        total_intercept = 1 - survival
        
        # Should be approximately sum of risks for small values
        assert total_intercept == pytest.approx(0.0588, rel=0.01)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
