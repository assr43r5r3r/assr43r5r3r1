"""
Bandwidth System for managing network link queues and throughput.

Implements per-link queuing, capacity simulation, and overload behavior.
"""

from typing import Dict, List, Optional, Tuple
from ..ecs_core import System, Entity
from ..components import NetworkLink, Signal
from ...settings import get_settings


class BandwidthSystem(System):
    """
    System for simulating network bandwidth and queuing.
    
    Features:
    - Per-link queue management
    - Capacity-based throughput simulation
    - Overload detection and packet loss
    - Queue growth mechanics
    """
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        
        # Link entity cache
        self._link_cache: Dict[Tuple[str, str], Entity] = {}
        
        # Queue statistics
        self.stats = {
            'total_bytes_queued': 0,
            'total_bytes_transmitted': 0,
            'packets_dropped': 0,
            'overloaded_links': 0
        }
        
        # Tick accumulator for fixed timestep
        self._tick_accumulator: float = 0.0
        self._tick_rate: float = 1.0 / 30.0  # 30 Hz
    
    def process(self, dt: float) -> None:
        """
        Process bandwidth simulation for one frame.
        
        Uses fixed timestep for deterministic simulation.
        """
        if not self.world:
            return
        
        self._tick_accumulator += dt
        
        # Process at fixed rate
        while self._tick_accumulator >= self._tick_rate:
            self._tick_accumulator -= self._tick_rate
            self._process_tick(self._tick_rate)
    
    def _process_tick(self, dt: float) -> None:
        """Process one simulation tick."""
        self._update_link_cache()
        self._process_queues(dt)
        self._update_stats()
    
    def _update_link_cache(self) -> None:
        """Update the link entity cache."""
        self._link_cache.clear()
        
        for entity, link in self.world.query_with_components(NetworkLink):
            self._link_cache[(link.a, link.b)] = entity
            self._link_cache[(link.b, link.a)] = entity
    
    def _process_queues(self, dt: float) -> None:
        """Process all link queues."""
        for entity, link in self.world.query_with_components(NetworkLink):
            if not link.active or not link.queue:
                continue
            
            # Calculate bytes that can be transmitted this tick
            bytes_available = int(link.bandwidth * dt)
            bytes_transmitted = 0
            
            # Process signals in queue
            signals_to_remove = []
            
            for signal_entity_id in link.queue[:]:  # Copy to allow modification
                signal_entity = self.world.get_entity(signal_entity_id)
                if not signal_entity or not signal_entity.alive:
                    signals_to_remove.append(signal_entity_id)
                    continue
                
                signal = self.world.get_component(signal_entity, Signal)
                if not signal:
                    signals_to_remove.append(signal_entity_id)
                    continue
                
                # Calculate bytes remaining for this signal on this edge
                bytes_remaining = signal.size - signal.bytes_transmitted
                
                # Transmit as much as possible
                bytes_to_send = min(bytes_available - bytes_transmitted, bytes_remaining)
                
                if bytes_to_send <= 0:
                    break
                
                signal.bytes_transmitted += bytes_to_send
                bytes_transmitted += bytes_to_send
                
                # Check if signal has finished traversing this edge
                if signal.bytes_transmitted >= signal.size:
                    signal.bytes_transmitted = 0
                    signal.progress = 1.0
                    signals_to_remove.append(signal_entity_id)
                else:
                    # Update progress
                    signal.progress = signal.bytes_transmitted / signal.size
            
            # Remove completed signals from queue
            for signal_id in signals_to_remove:
                if signal_id in link.queue:
                    link.queue.remove(signal_id)
            
            # Update current load
            link.current_load = sum(
                self._get_signal_remaining_bytes(sid)
                for sid in link.queue
            )
            
            self.stats['total_bytes_transmitted'] += bytes_transmitted
    
    def _get_signal_remaining_bytes(self, signal_entity_id: int) -> int:
        """Get remaining bytes for a signal."""
        if not self.world:
            return 0
        
        entity = self.world.get_entity(signal_entity_id)
        if not entity or not entity.alive:
            return 0
        
        signal = self.world.get_component(entity, Signal)
        if not signal:
            return 0
        
        return signal.size - signal.bytes_transmitted
    
    def _update_stats(self) -> None:
        """Update bandwidth statistics."""
        self.stats['total_bytes_queued'] = 0
        self.stats['overloaded_links'] = 0
        
        for entity, link in self.world.query_with_components(NetworkLink):
            self.stats['total_bytes_queued'] += link.current_load
            
            # Check for overload
            threshold = link.bandwidth * self.settings.QUEUE_THRESHOLD_MULTIPLIER
            if link.current_load > threshold:
                self.stats['overloaded_links'] += 1
    
    def enqueue_signal(self, signal_entity: Entity, 
                       from_node: str, to_node: str) -> bool:
        """
        Add a signal to a link's queue.
        
        Args:
            signal_entity: Signal entity to enqueue
            from_node: Source node ID
            to_node: Destination node ID
            
        Returns:
            True if successfully enqueued
        """
        link_entity = self._link_cache.get((from_node, to_node))
        if not link_entity:
            return False
        
        link = self.world.get_component(link_entity, NetworkLink)
        if not link or not link.active:
            return False
        
        # Check for queue overflow
        signal = self.world.get_component(signal_entity, Signal)
        if not signal:
            return False
        
        threshold = link.bandwidth * self.settings.QUEUE_THRESHOLD_MULTIPLIER
        if link.current_load + signal.size > threshold * 2:
            # Queue overflow - packet loss
            self.stats['packets_dropped'] += 1
            if self.world:
                self.world.emit_event('signal_dropped',
                                     signal_id=signal_entity.id,
                                     reason='queue_overflow',
                                     link_a=from_node,
                                     link_b=to_node)
            return False
        
        # Add to queue
        link.queue.append(signal_entity.id)
        link.current_load += signal.size
        signal.state = 'queued'
        
        return True
    
    def get_link_load(self, from_node: str, to_node: str) -> float:
        """
        Get the load ratio of a link (0.0 - 1.0+).
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            
        Returns:
            Load ratio (current_load / bandwidth)
        """
        link_entity = self._link_cache.get((from_node, to_node))
        if not link_entity:
            return 0.0
        
        link = self.world.get_component(link_entity, NetworkLink)
        if not link:
            return 0.0
        
        return link.current_load / max(link.bandwidth, 1)
    
    def get_effective_latency(self, from_node: str, to_node: str) -> float:
        """
        Get the effective latency including congestion delays.
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            
        Returns:
            Effective latency in seconds
        """
        link_entity = self._link_cache.get((from_node, to_node))
        if not link_entity:
            return float('inf')
        
        link = self.world.get_component(link_entity, NetworkLink)
        if not link:
            return float('inf')
        
        return link.get_effective_latency()
    
    def get_packet_loss_probability(self, from_node: str, to_node: str) -> float:
        """
        Calculate packet loss probability based on queue state.
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            
        Returns:
            Packet loss probability (0.0 - 1.0)
        """
        load = self.get_link_load(from_node, to_node)
        
        # No loss below threshold
        if load < 1.0:
            return 0.0
        
        # Increasing loss probability as queue grows
        excess = load - 1.0
        base_loss = self.settings.PACKET_LOSS_BASE
        
        return min(1.0, base_loss + excess * 0.1)
    
    def is_link_congested(self, from_node: str, to_node: str) -> bool:
        """Check if a link is congested (load > threshold)."""
        return self.get_link_load(from_node, to_node) > 1.0
    
    def clear_link_queue(self, from_node: str, to_node: str) -> int:
        """
        Clear all signals from a link's queue.
        
        Returns:
            Number of signals cleared
        """
        link_entity = self._link_cache.get((from_node, to_node))
        if not link_entity:
            return 0
        
        link = self.world.get_component(link_entity, NetworkLink)
        if not link:
            return 0
        
        count = len(link.queue)
        link.queue.clear()
        link.current_load = 0
        
        return count
