# compensation/signals.py
"""
Signal handlers for the compensation app.

Listens to measurement signals and triggers compensation processing.
"""

import logging
from django.dispatch import receiver

from measurement.signals import measurement_captured, capture_completed

logger = logging.getLogger(__name__)


@receiver(measurement_captured)
def handle_measurement_captured(sender, measurement, feature_result=None, **kwargs):
    """
    Handle a single measurement capture.
    
    Triggers compensation processing for the measurement.
    """
    from .engine import get_engine
    
    try:
        engine = get_engine()
        results = engine.process(measurement)
        
        # Update feature_result with compensation info if provided
        if feature_result and results:
            for result in results:
                if result.triggered:
                    feature_result['compensation_triggered'] = True
                    feature_result['offset_sent'] = result.offset_applied
                    feature_result['accumulated_after'] = result.accumulated_after
                    feature_result['usage_percentage'] = result.usage_percentage
                    break  # Use first triggered result
        
        logger.debug(
            f"Processed compensation for measurement {measurement.id}: "
            f"{len(results)} rules evaluated"
        )
        
    except Exception as e:
        logger.exception(f"Error processing compensation for measurement {measurement.id}")


@receiver(capture_completed)
def handle_capture_completed(sender, measurements=None, capture_result=None, **kwargs):
    """
    Handle completion of a capture batch.
    
    Could be used for batch processing or summary logging.
    """
    if measurements:
        logger.debug(f"Capture completed: {len(measurements)} measurements")
