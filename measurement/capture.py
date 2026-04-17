# measurement/capture.py
"""
Core measurement capture logic.

This is the heart of the measurement layer. Called by:
- Manual CAPTURE button (via WebSocket)
- Automatic trigger from controller CYCLE_COMPLETE signal
- Simulator for testing

Flow:
    1. Read current channel values from gauge (or accept passed values)
    2. Evaluate feature formulas
    3. Check tolerances
    4. Save Measurement records
    5. Emit signals (compensation subscribes separately)
    6. Broadcast results via WebSocket
    7. Return results

NOTE: Compensation logic has been moved to compensation/engine.py
      This module now emits signals that compensation subscribes to.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from django.utils import timezone
from django.db import transaction

from .models import (
    Feature, FeatureInput, Measurement, 
    GaugeConfig, ChannelConfig,
    ToleranceMode
)
from .signals import measurement_captured, capture_completed

logger = logging.getLogger(__name__)


@dataclass
class ChannelReading:
    """A single channel reading."""
    channel_index: int
    value: float
    timestamp: datetime
    channel_name: str = ""


@dataclass 
class FeatureResult:
    """Result of evaluating a single feature."""
    feature_id: int
    feature_name: str
    computed_value: float
    deviation: float
    nominal: Optional[float]
    tolerance_upper: Optional[float]
    tolerance_lower: Optional[float]
    in_tolerance: bool
    in_warning: bool
    status: str  # OK, WARN, ALARM, NONE
    unit: str
    formula: str
    inputs_used: Dict[str, float]  # {'A': 0.012, 'B': -0.003}
    measurement_id: Optional[int] = None  # Set after saving
    
    # Set by compensation signal handler
    compensation_triggered: bool = False
    offset_sent: Optional[float] = None
    accumulated_after: Optional[float] = None
    usage_percentage: Optional[float] = None


@dataclass
class CaptureResult:
    """Complete result of a capture operation."""
    success: bool
    timestamp: datetime
    source: str  # 'manual', 'auto', 'simulator'
    channel_readings: Dict[int, float]
    feature_results: List[FeatureResult]
    errors: List[str] = field(default_factory=list)
    
    @property
    def all_pass(self) -> bool:
        """True if all features with tolerances are in tolerance."""
        return all(
            r.in_tolerance or r.in_tolerance is None 
            for r in self.feature_results
        )
    
    @property
    def any_alarm(self) -> bool:
        """True if any feature is out of tolerance."""
        return any(r.status == 'ALARM' for r in self.feature_results)
    
    @property
    def any_warning(self) -> bool:
        """True if any feature is in warning zone."""
        return any(r.status == 'WARN' for r in self.feature_results)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for WebSocket."""
        return {
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'all_pass': self.all_pass,
            'any_alarm': self.any_alarm,
            'any_warning': self.any_warning,
            'channels': {str(k): v for k, v in self.channel_readings.items()},
            'features': [
                {
                    'id': r.feature_id,
                    'name': r.feature_name,
                    'value': r.computed_value,
                    'deviation': r.deviation,
                    'nominal': r.nominal,
                    'status': r.status,
                    'in_tolerance': r.in_tolerance,
                    'in_warning': r.in_warning,
                    'unit': r.unit,
                    'measurement_id': r.measurement_id,
                    'compensation_triggered': r.compensation_triggered,
                    'offset_sent': r.offset_sent,
                    'accumulated_after': r.accumulated_after,
                    'usage_percentage': r.usage_percentage,
                }
                for r in self.feature_results
            ],
            'errors': self.errors,
        }


class CaptureService:
    """
    Service for capturing measurements.
    
    Usage:
        service = CaptureService()
        
        # Manual capture with live gauge readings
        result = service.capture()
        
        # Capture with specific channel values (for testing/simulator)
        result = service.capture(channel_values={0: 12.70, 1: 12.71})
        
        # Capture specific features only
        result = service.capture(feature_ids=[1, 2])
    """
    
    def __init__(self):
        self._gauge_service = None
    
    @property
    def gauge_service(self):
        """Lazy load gauge service to avoid circular imports."""
        if self._gauge_service is None:
            from .services import get_service
            self._gauge_service = get_service()
        return self._gauge_service
    
    def capture(
        self,
        channel_values: Optional[Dict[int, float]] = None,
        feature_ids: Optional[List[int]] = None,
        source: str = 'manual',
        save_to_db: bool = True,
        trigger_compensation: bool = True,
        broadcast: bool = True,
    ) -> CaptureResult:
        """
        Execute a measurement capture.
        
        Args:
            channel_values: Dict of channel_index -> value. If None, reads from live gauge.
            feature_ids: List of feature IDs to evaluate. If None, evaluates all active features.
            source: Source identifier ('manual', 'auto', 'simulator', etc.)
            save_to_db: Whether to save Measurement records to database.
            trigger_compensation: Whether to emit signals for compensation processing.
            broadcast: Whether to broadcast results via WebSocket.
        
        Returns:
            CaptureResult with all feature evaluations.
        """
        timestamp = timezone.now()
        errors = []
        
        # Get channel values
        if channel_values is None:
            channel_values, read_errors = self._read_live_channels()
            errors.extend(read_errors)
            if not channel_values:
                return CaptureResult(
                    success=False,
                    timestamp=timestamp,
                    source=source,
                    channel_readings={},
                    feature_results=[],
                    errors=errors or ["No channel readings available"],
                )
        
        # Get features to evaluate
        features = self._get_features(feature_ids)
        if not features:
            return CaptureResult(
                success=False,
                timestamp=timestamp,
                source=source,
                channel_readings=channel_values,
                feature_results=[],
                errors=["No active features to evaluate"],
            )
        
        # Evaluate each feature
        feature_results = []
        measurements = []
        
        for feature in features:
            result = self._evaluate_feature(feature, channel_values)
            if result:
                feature_results.append(result)
        
        # Save to database
        if save_to_db and feature_results:
            measurements = self._save_measurements(feature_results, channel_values, source, timestamp)
        
        # Emit signals for compensation (subscribers handle the rest)
        if trigger_compensation and measurements:
            self._emit_measurement_signals(measurements, feature_results)
        
        # Build result
        capture_result = CaptureResult(
            success=True,
            timestamp=timestamp,
            source=source,
            channel_readings=channel_values,
            feature_results=feature_results,
            errors=errors,
        )
        
        # Emit capture completed signal
        capture_completed.send(
            sender=self.__class__,
            measurements=measurements,
            capture_result=capture_result
        )
        
        # Broadcast via WebSocket
        if broadcast:
            self._broadcast_result(capture_result)
        
        logger.info(
            f"Capture complete: {len(feature_results)} features, "
            f"pass={capture_result.all_pass}, source={source}"
        )
        
        return capture_result
    
    def _read_live_channels(self) -> tuple[Dict[int, float], List[str]]:
        """Read current values from live gauge."""
        errors = []
        channel_values = {}
        
        try:
            service = self.gauge_service
            if not service.is_running:
                return {}, ["Gauge service not running"]
            
            stats = service.get_all_stats()
            for channel_index, stat in stats.items():
                if stat.last_value is not None:
                    channel_values[channel_index] = stat.last_value
                else:
                    errors.append(f"No reading for channel {channel_index}")
        
        except Exception as e:
            logger.exception("Error reading live channels")
            errors.append(f"Gauge read error: {str(e)}")
        
        return channel_values, errors
    
    def _get_features(self, feature_ids: Optional[List[int]] = None) -> List[Feature]:
        """Get features to evaluate."""
        queryset = Feature.objects.filter(active=True).prefetch_related('inputs')
        
        if feature_ids:
            queryset = queryset.filter(id__in=feature_ids)
        
        return list(queryset)
    
    def _evaluate_feature(
        self, 
        feature: Feature, 
        channel_values: Dict[int, float]
    ) -> Optional[FeatureResult]:
        """Evaluate a single feature against channel values."""
        try:
            # Build inputs dict
            inputs_used = {}
            for inp in feature.inputs.all():
                value = channel_values.get(inp.channel_index)
                if value is None:
                    logger.warning(
                        f"Feature {feature.name}: missing channel {inp.channel_index} for input {inp.label}"
                    )
                    return None
                inputs_used[inp.label] = value
            
            # Evaluate formula
            computed_value = feature.evaluate_formula(channel_values)
            if computed_value is None:
                logger.warning(f"Feature {feature.name}: formula evaluation failed")
                return None
            
            # Evaluate tolerance
            tol_result = feature.evaluate_tolerance(computed_value)
            
            return FeatureResult(
                feature_id=feature.id,
                feature_name=feature.name,
                computed_value=computed_value,
                deviation=tol_result['deviation'],
                nominal=feature.nominal,
                tolerance_upper=feature.tolerance_upper,
                tolerance_lower=feature.tolerance_lower,
                in_tolerance=tol_result['in_tolerance'],
                in_warning=tol_result['in_warning'],
                status=tol_result['status'],
                unit=feature.unit,
                formula=feature.formula,
                inputs_used=inputs_used,
            )
        
        except Exception as e:
            logger.exception(f"Error evaluating feature {feature.name}")
            return None
    
    @transaction.atomic
    def _save_measurements(
        self,
        results: List[FeatureResult],
        channel_values: Dict[int, float],
        source: str,
        timestamp: datetime,
    ) -> List[Measurement]:
        """Save measurement records to database."""
        measurements = []
        
        for result in results:
            try:
                measurement = Measurement.objects.create(
                    feature_id=result.feature_id,
                    channel_values=channel_values,
                    computed_value=result.computed_value,
                    deviation=result.deviation,
                    in_tolerance=result.in_tolerance if result.in_tolerance is not None else True,
                    in_warning=result.in_warning,
                    status=result.status,
                    timestamp=timestamp,
                    source=source,
                )
                result.measurement_id = measurement.id
                measurements.append(measurement)
            except Exception as e:
                logger.exception(f"Error saving measurement for {result.feature_name}")
        
        return measurements
    
    def _emit_measurement_signals(
        self,
        measurements: List[Measurement],
        feature_results: List[FeatureResult]
    ):
        """Emit signals for each measurement (compensation subscribes to these)."""
        # Build lookup for feature results
        result_by_feature_id = {r.feature_id: r for r in feature_results}
        
        for measurement in measurements:
            feature_result = result_by_feature_id.get(measurement.feature_id)
            
            # Convert to mutable dict for signal handler to update
            result_dict = {
                'feature_id': measurement.feature_id,
                'deviation': measurement.deviation,
                'status': measurement.status,
                'compensation_triggered': False,
                'offset_sent': None,
                'accumulated_after': None,
                'usage_percentage': None,
            }
            
            # Emit signal - compensation handler will process and update result_dict
            measurement_captured.send(
                sender=self.__class__,
                measurement=measurement,
                feature_result=result_dict
            )
            
            # Update the FeatureResult with compensation info
            if feature_result and result_dict.get('compensation_triggered'):
                feature_result.compensation_triggered = True
                feature_result.offset_sent = result_dict.get('offset_sent')
                feature_result.accumulated_after = result_dict.get('accumulated_after')
                feature_result.usage_percentage = result_dict.get('usage_percentage')
    
    def _broadcast_result(self, result: CaptureResult):
        """Broadcast capture result via WebSocket."""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            
            message = {
                'type': 'capture_result',
                **result.to_dict()
            }
            
            async_to_sync(channel_layer.group_send)(
                'gauge_all',
                message
            )
        except Exception as e:
            logger.warning(f"Error broadcasting capture result: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_capture_service: Optional[CaptureService] = None


def get_capture_service() -> CaptureService:
    """Get the singleton capture service instance."""
    global _capture_service
    if _capture_service is None:
        _capture_service = CaptureService()
    return _capture_service


def capture_measurement(
    channel_values: Optional[Dict[int, float]] = None,
    feature_ids: Optional[List[int]] = None,
    source: str = 'manual',
    **kwargs
) -> CaptureResult:
    """
    Convenience function for capturing measurements.
    
    Usage:
        # Capture all features with live readings
        result = capture_measurement()
        
        # Capture with simulated values
        result = capture_measurement(
            channel_values={0: 12.70, 1: 12.71, 2: 50.01, 3: 0.008},
            source='simulator'
        )
    """
    service = get_capture_service()
    return service.capture(
        channel_values=channel_values,
        feature_ids=feature_ids,
        source=source,
        **kwargs
    )
