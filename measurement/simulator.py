# measurement/simulator.py
"""
Simulates gauge readings for testing without hardware.
"""

import time
import random
import threading
from datetime import datetime
from typing import Dict, Optional, Callable
from django.utils import timezone


class GaugeSimulator:
    """
    Simulates gauge readings for multiple channels.
    
    Usage:
        from measurement.simulator import GaugeSimulator
        
        sim = GaugeSimulator()
        sim.start()
        # Dashboard will show live readings
        sim.stop()
    """
    
    def __init__(
        self,
        rate_hz: float = 5.0,
        drift: bool = True,
        auto_capture: bool = False,
        capture_interval: float = 5.0,
    ):
        self.rate_hz = rate_hz
        self.drift = drift
        self.auto_capture = auto_capture
        self.capture_interval = capture_interval
        
        self._thread = None
        self._stop_event = threading.Event()
        
        # Channel configurations: {channel_index: {nominal, variation, current}}
        self._channels: Dict[int, dict] = {
            0: {'nominal': 12.700, 'variation': 0.008, 'current': 12.700, 'drift_dir': 1, 'name': 'OD Left'},
            1: {'nominal': 12.700, 'variation': 0.008, 'current': 12.700, 'drift_dir': 1, 'name': 'OD Right'},
            2: {'nominal': 50.000, 'variation': 0.020, 'current': 50.000, 'drift_dir': 1, 'name': 'Face'},
            3: {'nominal': 0.000, 'variation': 0.010, 'current': 0.000, 'drift_dir': 1, 'name': 'TIR'},
        }
        
        self._last_capture_time = 0
        self._on_reading: Optional[Callable] = None
    
    def configure_channel(self, channel: int, nominal: float, variation: float, name: str = ""):
        """Configure a channel's simulation parameters."""
        self._channels[channel] = {
            'nominal': nominal,
            'variation': variation,
            'current': nominal,
            'drift_dir': 1,
            'name': name or f'CH{channel + 1}',
        }
    
    def start(self):
        """Start simulating readings."""
        self._stop_event.clear()
        self._last_capture_time = time.time()
        self._thread = threading.Thread(target=self._simulate_loop, daemon=True)
        self._thread.start()
        print(f"Simulator started: {len(self._channels)} channels @ {self.rate_hz} Hz")
        if self.auto_capture:
            print(f"Auto-capture every {self.capture_interval}s")
    
    def stop(self):
        """Stop simulating."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        print("Simulator stopped")
    
    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
    
    def get_current_values(self) -> Dict[int, float]:
        """Get current simulated values for all channels."""
        return {ch: cfg['current'] for ch, cfg in self._channels.items()}
    
    def _simulate_loop(self):
        """Generate fake readings and broadcast."""
        from dashboard.consumers import broadcast_reading
        
        interval = 1.0 / self.rate_hz
        
        while not self._stop_event.is_set():
            now = timezone.now()
            channel_values = {}
            
            for channel, cfg in self._channels.items():
                # Generate realistic value with noise and drift
                noise = random.gauss(0, cfg['variation'] / 4)
                
                if self.drift:
                    # Slow drift to simulate tool wear
                    drift_amount = random.uniform(0.0001, 0.0003)
                    cfg['current'] += cfg['drift_dir'] * drift_amount
                    
                    # Reverse direction near edges
                    if abs(cfg['current'] - cfg['nominal']) > cfg['variation'] * 0.9:
                        cfg['drift_dir'] *= -1
                
                value = cfg['current'] + noise
                
                # TIR is always positive (absolute value)
                if channel == 3:
                    value = abs(value)
                
                channel_values[channel] = value
                
                # Check tolerance for this channel
                if channel == 3:  # TIR - limit mode
                    in_tolerance = value <= cfg['variation']
                else:
                    deviation = value - cfg['nominal']
                    in_tolerance = abs(deviation) <= cfg['variation']
                
                # Broadcast individual channel reading
                try:
                    broadcast_reading(channel, value, now, in_tolerance)
                except Exception as e:
                    pass  # Don't spam errors
                
                # Callback if set
                if self._on_reading:
                    self._on_reading(channel, value, now, in_tolerance)
            
            # Auto-capture if enabled
            if self.auto_capture:
                if time.time() - self._last_capture_time >= self.capture_interval:
                    self._do_capture(channel_values)
                    self._last_capture_time = time.time()
            
            time.sleep(interval)
    
    def _do_capture(self, channel_values: Dict[int, float]):
        """Execute a capture with current values."""
        try:
            from measurement.capture import capture_measurement
            result = capture_measurement(
                channel_values=channel_values,
                source='simulator'
            )
            
            status = "PASS" if result.all_pass else "FAIL"
            features = ", ".join(
                f"{r.feature_name}:{r.status}" 
                for r in result.feature_results
            )
            print(f"[Simulator] Capture: {status} - {features}")
        except Exception as e:
            print(f"[Simulator] Capture error: {e}")
    
    def trigger_capture(self):
        """Manually trigger a capture with current values."""
        channel_values = self.get_current_values()
        self._do_capture(channel_values)
    
    def induce_drift(self, channel: int, amount: float):
        """
        Manually induce drift on a channel (simulate tool wear).
        Positive = part getting bigger, negative = part getting smaller.
        """
        if channel in self._channels:
            self._channels[channel]['current'] += amount
            print(f"[Simulator] CH{channel + 1} drift: {amount:+.4f}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_simulator_instance: Optional[GaugeSimulator] = None


def get_simulator() -> GaugeSimulator:
    """Get the singleton simulator instance."""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = GaugeSimulator()
    return _simulator_instance


def start_simulator(
    rate_hz: float = 5.0,
    auto_capture: bool = False,
    capture_interval: float = 5.0,
) -> GaugeSimulator:
    """Start the simulator."""
    global _simulator_instance
    
    if _simulator_instance and _simulator_instance.is_running:
        print("Simulator already running")
        return _simulator_instance
    
    _simulator_instance = GaugeSimulator(
        rate_hz=rate_hz,
        auto_capture=auto_capture,
        capture_interval=capture_interval,
    )
    _simulator_instance.start()
    return _simulator_instance


def stop_simulator():
    """Stop the simulator."""
    global _simulator_instance
    if _simulator_instance:
        _simulator_instance.stop()


def run_simulator(duration: Optional[float] = None, **kwargs):
    """
    Convenience function to run simulator.
    
    Usage:
        python manage.py shell
        >>> from measurement.simulator import run_simulator
        >>> run_simulator(duration=30)  # Run for 30 seconds
        >>> run_simulator(auto_capture=True)  # Run with auto-capture
    """
    sim = start_simulator(**kwargs)
    
    try:
        if duration:
            time.sleep(duration)
            sim.stop()
        else:
            print("Press Ctrl+C to stop...")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        sim.stop()
