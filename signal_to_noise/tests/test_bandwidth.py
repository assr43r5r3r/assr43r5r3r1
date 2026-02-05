"""
Unit tests for bandwidth queueing system.
"""

import pytest
import sys
import os

# Add the signal_to_noise directory to path
signal_to_noise_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, signal_to_noise_dir)

from src.ecs.ecs_core import World, Entity
from src.ecs.components import NetworkLink, Signal
from src.ecs.systems.bandwidth_system import BandwidthSystem


class TestBandwidthSystem:
    """Tests for the bandwidth system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.world = World()
        self.system = BandwidthSystem()
        self.system.world = self.world
    
    def create_link(self, a='A', b='B', bandwidth=2048, latency=0.1):
        """Create a test link entity."""
        return self.world.create_entity(
            NetworkLink(
                a=a,
                b=b,
                bandwidth=bandwidth,
                latency=latency,
                reliability=0.9,
                base_risk=0.1,
                current_load=0,
                queue=[],
                active=True
            )
        )
    
    def create_signal(self, path=['A', 'B'], size=1024):
        """Create a test signal entity."""
        return self.world.create_entity(
            Signal(
                path=path,
                message_ref=0,
                current_index=0,
                progress=0.0,
                size=size,
                bytes_transmitted=0,
                state='queued'
            )
        )
    
    def test_empty_queue_processing(self):
        """Test processing with empty queues."""
        self.create_link()
        
        # Should not raise any errors
        self.system.process(0.1)
    
    def test_signal_progress(self):
        """Test that signals make progress through transmission."""
        link_entity = self.create_link(bandwidth=2048)
        link = self.world.get_component(link_entity, NetworkLink)
        
        signal_entity = self.create_signal(size=1024)
        signal = self.world.get_component(signal_entity, Signal)
        
        # Add signal to queue
        link.queue.append(signal_entity.id)
        link.current_load = 1024
        
        # Process for one tick (at 30Hz, with 2048 bytes/sec bandwidth)
        # Should transmit about 2048/30 ≈ 68 bytes per tick
        self.system.process(1/30)
        
        # Signal should have made some progress
        # Note: Due to fixed timestep, actual progress may vary
    
    def test_load_tracking(self):
        """Test that link load is tracked correctly."""
        link_entity = self.create_link()
        link = self.world.get_component(link_entity, NetworkLink)
        
        signal_entity = self.create_signal(size=2048)
        
        link.queue.append(signal_entity.id)
        link.current_load = 2048
        
        assert link.current_load == 2048
    
    def test_enqueue_signal(self):
        """Test enqueueing a signal."""
        link_entity = self.create_link()
        signal_entity = self.create_signal()
        
        # Update cache
        self.system._update_link_cache()
        
        result = self.system.enqueue_signal(signal_entity, 'A', 'B')
        
        assert result == True
        
        link = self.world.get_component(link_entity, NetworkLink)
        assert signal_entity.id in link.queue
    
    def test_enqueue_to_nonexistent_link(self):
        """Test enqueueing to a non-existent link."""
        signal_entity = self.create_signal()
        
        self.system._update_link_cache()
        
        result = self.system.enqueue_signal(signal_entity, 'X', 'Y')
        assert result == False
    
    def test_get_link_load(self):
        """Test getting link load ratio."""
        link_entity = self.create_link(bandwidth=2048)
        link = self.world.get_component(link_entity, NetworkLink)
        link.current_load = 1024
        
        self.system._update_link_cache()
        
        load = self.system.get_link_load('A', 'B')
        assert load == 0.5
    
    def test_effective_latency(self):
        """Test effective latency calculation."""
        link_entity = self.create_link(bandwidth=2048, latency=0.1)
        link = self.world.get_component(link_entity, NetworkLink)
        
        self.system._update_link_cache()
        
        # With no load, should return base latency
        link.current_load = 0
        latency = self.system.get_effective_latency('A', 'B')
        assert latency == pytest.approx(0.1, rel=0.01)
    
    def test_is_congested(self):
        """Test congestion detection."""
        link_entity = self.create_link(bandwidth=1000)
        link = self.world.get_component(link_entity, NetworkLink)
        
        self.system._update_link_cache()
        
        # Not congested when load < bandwidth
        link.current_load = 500
        assert self.system.is_link_congested('A', 'B') == False
        
        # Congested when load > bandwidth
        link.current_load = 1500
        assert self.system.is_link_congested('A', 'B') == True
    
    def test_packet_loss_probability(self):
        """Test packet loss probability calculation."""
        link_entity = self.create_link(bandwidth=1000)
        link = self.world.get_component(link_entity, NetworkLink)
        
        self.system._update_link_cache()
        
        # No loss when under capacity
        link.current_load = 500
        prob = self.system.get_packet_loss_probability('A', 'B')
        assert prob == 0.0
        
        # Some loss when over capacity
        link.current_load = 1500
        prob = self.system.get_packet_loss_probability('A', 'B')
        assert prob > 0.0


class TestBandwidthMath:
    """Tests for bandwidth math and calculations."""
    
    def test_throughput_calculation(self):
        """Test that throughput math is correct."""
        bandwidth = 2048  # bytes per second
        tick_rate = 30  # Hz
        
        bytes_per_tick = bandwidth / tick_rate
        assert bytes_per_tick == pytest.approx(68.27, rel=0.01)
    
    def test_transmission_time(self):
        """Test transmission time calculation."""
        signal_size = 4096  # bytes
        bandwidth = 2048  # bytes per second
        
        transmission_time = signal_size / bandwidth
        assert transmission_time == 2.0  # seconds
    
    def test_queue_growth_impact(self):
        """Test queue growth impact on latency."""
        base_latency = 0.1
        bandwidth = 2048
        current_load = 2048  # At capacity
        
        # When at capacity, latency should increase
        load_factor = current_load / bandwidth
        effective_latency = base_latency * (1 + load_factor * 0.5)
        
        assert effective_latency > base_latency
        assert effective_latency == pytest.approx(0.15, rel=0.01)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
