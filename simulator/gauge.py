# simulator/gauge.py
"""
Simulated gauge readings based on tool wear and compensation.

This is where physics meets simulation:
  reading = nominal - wear + offset + random_variation
"""

import random
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from simulator.plc import TestPLC
    from simulator.tool_wear import ToolWearSimulation


# Channel configuration
CHANNEL_CONFIG = {
    0: {
        'name': 'OD Left',
        'nominal': 12.700,
        'tool': 1,
        'axis': 'X',
        'wear_direction': -1,
        'variation': 0.002,
    },
    1: {
        'name': 'OD Right',
        'nominal': 12.700,
        'tool': 1,
        'axis': 'X',
        'wear_direction': -1,
        'variation': 0.002,
    },
    2: {
        'name': 'Face',
        'nominal': 50.000,
        'tool': 2,
        'axis': 'Z',
        'wear_direction': -1,
        'variation': 0.003,
    },
    3: {
        'name': 'TIR',
        'nominal': 0.000,
        'tool': None,
        'axis': None,
        'wear_direction': 0,
        'variation': 0.004,
    },
}


def simulate_gauge_readings(
    plc: 'TestPLC',
    tool_wear: 'ToolWearSimulation'
) -> Dict[int, float]:
    """
    Simulate what the gauge would read.
    
    For each channel:
      reading = nominal + (wear * wear_direction) + offset + variation
    """
    readings = {}
    
    for channel, config in CHANNEL_CONFIG.items():
        nominal = config['nominal']
        variation = random.gauss(0, config['variation'])
        
        tool_effect = 0.0
        
        if config['tool'] is not None:
            tool = config['tool']
            axis = config['axis']
            wear_dir = config['wear_direction']
            
            wear = tool_wear.get_wear(tool) if tool_wear else 0.0
            offset = plc.read_offset(tool, axis)
            
            tool_effect = (wear * wear_dir) + offset
        
        readings[channel] = nominal + tool_effect + variation
    
    return readings


def get_channel_config() -> Dict[int, dict]:
    """Get channel configuration (for dashboard display)."""
    return CHANNEL_CONFIG.copy()