"""
Signal System for managing signal progression through the network.

Handles signal movement, delivery, interception, and callbacks.
"""

import random
from typing import Dict, List, Optional, Any
from ..ecs_core import System, Entity
from ..components import Signal, Message, NetworkNode, NetworkLink, Faction
from ...settings import get_settings


class SignalSystem(System):
    """
    System for processing active signals in the network.
    
    Features:
    - Signal progression along paths
    - Delivery handling
    - Interception probability calculations
    - Post-delivery callbacks
    """
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        
        # Active signal count for performance limits
        self.active_signal_count: int = 0
        
        # Pending signals (when over limit)
        self.pending_signals: List[int] = []
        
        # Statistics
        self.stats = {
            'signals_delivered': 0,
            'signals_intercepted': 0,
            'signals_dropped': 0,
            'signals_active': 0
        }
        
        # Tick accumulator for fixed timestep
        self._tick_accumulator: float = 0.0
        self._tick_rate: float = 1.0 / 30.0
    
    def process(self, dt: float) -> None:
        """Process all active signals."""
        if not self.world:
            return
        
        self._tick_accumulator += dt
        
        while self._tick_accumulator >= self._tick_rate:
            self._tick_accumulator -= self._tick_rate
            self._process_tick(self._tick_rate)
    
    def _process_tick(self, dt: float) -> None:
        """Process one simulation tick."""
        self._count_active_signals()
        self._spawn_pending_signals()
        self._progress_signals(dt)
        self._handle_completed_signals()
        self._update_ttl(dt)
    
    def _count_active_signals(self) -> None:
        """Count currently active signals."""
        count = 0
        for entity, signal in self.world.query_with_components(Signal):
            if signal.state in ('traveling', 'queued'):
                count += 1
        
        self.active_signal_count = count
        self.stats['signals_active'] = count
    
    def _spawn_pending_signals(self) -> None:
        """Spawn pending signals if under the limit."""
        max_signals = self.settings.MAX_CONCURRENT_SIGNALS
        
        while self.pending_signals and self.active_signal_count < max_signals:
            signal_id = self.pending_signals.pop(0)
            entity = self.world.get_entity(signal_id)
            if entity and entity.alive:
                signal = self.world.get_component(entity, Signal)
                if signal and signal.state == 'pending':
                    signal.state = 'traveling'
                    self.active_signal_count += 1
    
    def _progress_signals(self, dt: float) -> None:
        """Progress signals along their paths."""
        for entity, signal in self.world.query_with_components(Signal):
            if signal.state != 'traveling':
                continue
            
            if not signal.path or signal.current_index >= len(signal.path) - 1:
                continue
            
            # Check if we need to move to next edge
            if signal.progress >= 1.0:
                self._advance_to_next_edge(entity, signal)
    
    def _advance_to_next_edge(self, entity: Entity, signal: Signal) -> None:
        """Move signal to the next edge in its path."""
        signal.current_index += 1
        signal.progress = 0.0
        signal.bytes_transmitted = 0
        
        if signal.current_index >= len(signal.path) - 1:
            # Reached destination
            signal.state = 'delivered'
            return
        
        # Check for interception at this node
        current_node = signal.path[signal.current_index]
        if self._check_interception(entity, signal, current_node):
            signal.state = 'intercepted'
            self.stats['signals_intercepted'] += 1
            if self.world:
                self.world.emit_event('signal_intercepted',
                                     signal_id=entity.id,
                                     location=current_node)
            return
        
        # Queue for next edge (bandwidth system will handle transmission)
        next_node = signal.path[signal.current_index + 1]
        signal.state = 'queued'
    
    def _check_interception(self, entity: Entity, signal: Signal, location: str) -> bool:
        """
        Check if a signal is intercepted at a location.
        
        P_intercept = base_risk * (1 - reliability) * attacker_presence * f(encryption)
        """
        # Get link data for interception probability
        if signal.current_index + 1 >= len(signal.path):
            return False
        
        next_node = signal.path[signal.current_index + 1]
        
        # Find link entity
        link = None
        for e, lnk in self.world.query_with_components(NetworkLink):
            if ((lnk.a == location and lnk.b == next_node) or
                (lnk.b == location and lnk.a == next_node)):
                link = lnk
                break
        
        if not link:
            return False
        
        # Calculate interception probability
        base_prob = link.base_risk * (1 - link.reliability)
        
        # Encryption reduces probability
        if signal.encrypted:
            encryption_factor = 0.5  # 50% reduction for encrypted
        else:
            encryption_factor = 1.0
        
        intercept_prob = base_prob * encryption_factor
        
        # Random roll
        return random.random() < intercept_prob
    
    def _handle_completed_signals(self) -> None:
        """Process delivered and intercepted signals."""
        signals_to_remove = []
        
        for entity, signal in self.world.query_with_components(Signal):
            if signal.state == 'delivered':
                self._on_signal_delivered(entity, signal)
                signals_to_remove.append(entity)
                self.stats['signals_delivered'] += 1
            
            elif signal.state == 'intercepted':
                self._on_signal_intercepted(entity, signal)
                signals_to_remove.append(entity)
            
            elif signal.state == 'dropped':
                self._on_signal_dropped(entity, signal)
                signals_to_remove.append(entity)
                self.stats['signals_dropped'] += 1
        
        # Remove completed signals
        for entity in signals_to_remove:
            self.world.remove_entity(entity)
    
    def _on_signal_delivered(self, entity: Entity, signal: Signal) -> None:
        """Handle successful signal delivery."""
        # Get associated message
        message = self._get_message(signal.message_ref)
        
        if message and self.world:
            # Emit delivery event
            self.world.emit_event('message_delivered',
                                 message_id=message.msg_id,
                                 dest=message.dest,
                                 reward=message.reward)
            
            # Update destination node stats
            dest_node = self._get_node(message.dest)
            if dest_node:
                dest_node.stats['messages_received'] = \
                    dest_node.stats.get('messages_received', 0) + 1
    
    def _on_signal_intercepted(self, entity: Entity, signal: Signal) -> None:
        """Handle signal interception."""
        message = self._get_message(signal.message_ref)
        
        if message and self.world:
            location = signal.path[signal.current_index] if signal.path else "unknown"
            self.world.emit_event('message_intercepted',
                                 message_id=message.msg_id,
                                 location=location)
    
    def _on_signal_dropped(self, entity: Entity, signal: Signal) -> None:
        """Handle dropped signal."""
        message = self._get_message(signal.message_ref)
        
        if message and self.world:
            self.world.emit_event('message_dropped',
                                 message_id=message.msg_id,
                                 reason='ttl_expired')
    
    def _update_ttl(self, dt: float) -> None:
        """Update time-to-live for all signals."""
        for entity, signal in self.world.query_with_components(Signal):
            if signal.state not in ('traveling', 'queued'):
                continue
            
            signal.ttl -= dt
            
            if signal.ttl <= 0:
                signal.state = 'dropped'
    
    def _get_message(self, message_ref: int) -> Optional[Message]:
        """Get message component by entity ID."""
        entity = self.world.get_entity(message_ref)
        if entity and entity.alive:
            return self.world.get_component(entity, Message)
        return None
    
    def _get_node(self, node_id: str) -> Optional[NetworkNode]:
        """Get node component by node ID."""
        for entity, node in self.world.query_with_components(NetworkNode):
            if node.node_id == node_id:
                return node
        return None
    
    def spawn_signal(self, message_entity: Entity, 
                     path: List[str],
                     encrypted: bool = False) -> Optional[Entity]:
        """
        Create a new signal entity for a message.
        
        Args:
            message_entity: Message entity to send
            path: Route as list of node IDs
            encrypted: Whether to encrypt the signal
            
        Returns:
            Signal entity, or None if creation failed
        """
        message = self.world.get_component(message_entity, Message)
        if not message or len(path) < 2:
            return None
        
        # Check signal limit
        if self.active_signal_count >= self.settings.MAX_CONCURRENT_SIGNALS:
            # Create as pending
            signal_entity = self.world.create_entity(
                Signal(
                    path=path,
                    message_ref=message_entity.id,
                    current_index=0,
                    progress=0.0,
                    ttl=message.meta.get('time_limit', 300.0),
                    encrypted=encrypted or message.encrypted,
                    size=message.size,
                    state='pending'
                )
            )
            self.pending_signals.append(signal_entity.id)
            return signal_entity
        
        # Create active signal
        signal_entity = self.world.create_entity(
            Signal(
                path=path,
                message_ref=message_entity.id,
                current_index=0,
                progress=0.0,
                ttl=message.meta.get('time_limit', 300.0),
                encrypted=encrypted or message.encrypted,
                size=message.size,
                state='traveling'
            )
        )
        
        # Update origin node stats
        origin_node = self._get_node(message.origin)
        if origin_node:
            origin_node.stats['messages_sent'] = \
                origin_node.stats.get('messages_sent', 0) + 1
        
        if self.world:
            self.world.emit_event('signal_spawned',
                                 signal_id=signal_entity.id,
                                 message_id=message.msg_id,
                                 path=path)
        
        return signal_entity
