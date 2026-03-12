# devices/simulator.py
"""
Simulates gauge readings for testing without hardware.
"""

import time
import random
import threading
from datetime import datetime
from django.utils import timezone


class GaugeSimulator:
    """
    Simulates gauge readings around a nominal value.
    
    Usage:
        from devices.simulator import GaugeSimulator
        
        sim = GaugeSimulator(nominal=25.400, variation=0.015)
        sim.start()
        # Dashboard will show live readings
        sim.stop()
    """
    
    def __init__(
        self,
        nominal: float = 25.400,
        variation: float = 0.010,
        rate_hz: float = 10.0,
        channel: int = 0,
        drift: bool = True
    ):
        self.nominal = nominal
        self.variation = variation
        self.rate_hz = rate_hz
        self.channel = channel
        self.drift = drift
        
        self._thread = None
        self._stop_event = threading.Event()
        self._current_value = nominal
        self._drift_direction = 1
    
    def start(self):
        """Start simulating readings."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._simulate_loop, daemon=True)
        self._thread.start()
        print(f"Simulator started: {self.nominal} ±{self.variation} mm @ {self.rate_hz} Hz")
    
    def stop(self):
        """Stop simulating."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        print("Simulator stopped")
    
    def _simulate_loop(self):
        """Generate fake readings and broadcast."""
        from dashboard.consumers import broadcast_reading
        
        interval = 1.0 / self.rate_hz
        
        while not self._stop_event.is_set():
            # Generate realistic value with noise and drift
            noise = random.gauss(0, self.variation / 3)
            
            if self.drift:
                # Slow drift toward edges of tolerance
                self._current_value += self._drift_direction * 0.0001
                if abs(self._current_value - self.nominal) > self.variation * 0.8:
                    self._drift_direction *= -1
            
            value = self._current_value + noise
            now = timezone.now()
            
            # Check tolerance
            deviation = value - self.nominal
            in_tolerance = abs(deviation) <= self.variation
            
            # Broadcast to WebSocket
            try:
                broadcast_reading(self.channel, value, now, in_tolerance)
            except Exception as e:
                print(f"Broadcast error: {e}")
            
            time.sleep(interval)


def run_simulator(nominal=25.400, variation=0.010, rate_hz=10.0, duration=None):
    """
    Convenience function to run simulator.
    
    Usage:
        python manage.py shell
        >>> from devices.simulator import run_simulator
        >>> run_simulator(duration=30)  # Run for 30 seconds
    """
    sim = GaugeSimulator(nominal=nominal, variation=variation, rate_hz=rate_hz)
    sim.start()
    
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