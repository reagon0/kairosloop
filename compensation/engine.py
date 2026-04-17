# compensation/engine.py
"""
Compensation Engine - Active service that processes measurements.

Listens for measurement signals, calculates required offsets,
and submits requests to the controller gateway.

This replaces the compensation logic that was embedded in capture.py.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass

from django.db import transaction

from .models import CompensationRule, CompensationEvent, CompensationStatus

logger = logging.getLogger(__name__)


@dataclass
class CompensationResult:
    """Result of processing a measurement through compensation."""
    rule_id: int
    feature_name: str
    tool_position: int
    deviation: float
    offset_calculated: float
    offset_applied: float
    status: str
    reason: str
    accumulated_after: float
    usage_percentage: float
    
    @property
    def triggered(self) -> bool:
        return self.status in ('APPLIED', 'ACCEPTED_WARNING')


class CompensationEngine:
    """
    Engine that processes measurements and applies compensation.
    
    Usage:
        engine = CompensationEngine()
        
        # Process a single measurement
        results = engine.process(measurement)
        
        # Or process a feature result directly
        results = engine.process_feature(feature_id, deviation, measurement_id)
    """
    
    def __init__(self):
        self._gateway = None
    
    @property
    def gateway(self):
        """Lazy load gateway to avoid circular imports."""
        if self._gateway is None:
            from controller.gateway import get_gateway
            self._gateway = get_gateway()
        return self._gateway
    
    def process(self, measurement) -> List[CompensationResult]:
        """
        Process a measurement and apply compensation if needed.
        
        Args:
            measurement: Measurement model instance
        
        Returns:
            List of CompensationResult for each rule that was evaluated
        """
        return self.process_feature(
            feature_id=measurement.feature_id,
            deviation=measurement.deviation,
            measurement_id=measurement.id
        )
    
    def process_feature(
        self,
        feature_id: int,
        deviation: float,
        measurement_id: Optional[int] = None
    ) -> List[CompensationResult]:
        """
        Process compensation for a feature's deviation.
        
        Args:
            feature_id: Feature that was measured
            deviation: Measured deviation from nominal
            measurement_id: Optional measurement record ID for logging
        
        Returns:
            List of CompensationResult for each applicable rule
        """
        from controller.gateway import OffsetRequest
        
        results = []
        
        # Get active compensation rules for this feature
        rules = CompensationRule.objects.filter(
            feature_id=feature_id,
            active=True
        ).select_related(
            'tool_assignment',
            'tool_assignment__tool_instance',
            'tool_assignment__tool_instance__tool_type',
            'tool_assignment__controller'
        )
        
        for rule in rules:
            result = self._process_rule(rule, deviation, measurement_id)
            if result:
                results.append(result)
        
        return results
    
    def _process_rule(
        self,
        rule: CompensationRule,
        deviation: float,
        measurement_id: Optional[int]
    ) -> Optional[CompensationResult]:
        """Process a single compensation rule."""
        from controller.gateway import OffsetRequest, OffsetDecision
        
        # Check if tool assignment exists and is valid
        if not rule.tool_assignment:
            logger.warning(f"Rule {rule.id} has no tool assignment - skipping")
            return None
        
        assignment = rule.tool_assignment
        
        # Validate the assignment chain
        if not hasattr(assignment, 'tool_instance') or not assignment.tool_instance:
            logger.warning(f"Rule {rule.id}: Assignment {assignment.id} has no tool_instance - skipping")
            return None
        
        if not hasattr(assignment.tool_instance, 'tool_type') or not assignment.tool_instance.tool_type:
            logger.warning(f"Rule {rule.id}: ToolInstance has no tool_type - skipping")
            return None
        
        # Calculate offset based on rule settings
        calc_result = rule.calculate_offset(deviation)
        
        if not calc_result['should_compensate']:
            logger.debug(f"Rule {rule.id}: skipped - {calc_result['reason']}")
            
            # Still log the event for tracking
            if measurement_id:
                self._log_event(
                    rule=rule,
                    measurement_id=measurement_id,
                    deviation=deviation,
                    calc_result=calc_result,
                    gateway_result=None
                )
            
            return CompensationResult(
                rule_id=rule.id,
                feature_name=rule.feature.name,
                tool_position=assignment.tool_position,
                deviation=deviation,
                offset_calculated=calc_result['offset_calculated'],
                offset_applied=0.0,
                status='SKIPPED',
                reason=calc_result['reason'],
                accumulated_after=abs(assignment.accumulated_offset),
                usage_percentage=assignment.usage_percentage,
            )
        
        # Submit to gateway
        request = OffsetRequest(
            tool_assignment_id=assignment.id,
            axis=rule.offset_axis,
            offset_value=calc_result['offset_to_apply'],
            source='compensation'
        )
        
        gateway_result = self.gateway.submit(request)
        
        # Map gateway decision to compensation status
        if gateway_result.decision == OffsetDecision.ACCEPTED:
            status = CompensationStatus.APPLIED
        elif gateway_result.decision == OffsetDecision.ACCEPTED_WARNING:
            status = CompensationStatus.APPLIED  # Still applied, just with warning
            logger.warning(
                f"Rule {rule.id}: {gateway_result.reason}"
            )
        elif gateway_result.decision == OffsetDecision.REJECTED_LIMIT:
            status = CompensationStatus.BLOCKED
            logger.warning(
                f"Rule {rule.id}: BLOCKED - {gateway_result.reason}"
            )
        elif gateway_result.decision == OffsetDecision.REJECTED_BLOCKED:
            status = CompensationStatus.BLOCKED
            logger.warning(
                f"Rule {rule.id}: BLOCKED - tool change required"
            )
        else:
            status = CompensationStatus.ERROR
            logger.error(
                f"Rule {rule.id}: ERROR - {gateway_result.reason}"
            )
        
        # Log the event
        if measurement_id:
            self._log_event(
                rule=rule,
                measurement_id=measurement_id,
                deviation=deviation,
                calc_result=calc_result,
                gateway_result=gateway_result
            )
        
        # Log to console
        if gateway_result.success:
            logger.info(
                f"Compensation: {rule.feature.name} → T{assignment.tool_position} "
                f"offset={gateway_result.offset_applied:+.6f} [{status}]"
            )
        
        return CompensationResult(
            rule_id=rule.id,
            feature_name=rule.feature.name,
            tool_position=assignment.tool_position,
            deviation=deviation,
            offset_calculated=calc_result['offset_calculated'],
            offset_applied=gateway_result.offset_applied,
            status=status.value if hasattr(status, 'value') else str(status),
            reason=gateway_result.reason,
            accumulated_after=gateway_result.accumulated_after,
            usage_percentage=gateway_result.usage_percentage,
        )
    
    @transaction.atomic
    def _log_event(
        self,
        rule: CompensationRule,
        measurement_id: int,
        deviation: float,
        calc_result: dict,
        gateway_result
    ):
        """Log a compensation event to the database."""
        from controller.gateway import OffsetDecision
        
        assignment = rule.tool_assignment
        
        # Determine status
        if gateway_result is None:
            status = CompensationStatus.SKIPPED
            offset_applied = 0.0
            accumulated_after = abs(assignment.accumulated_offset)
            reason = calc_result.get('reason', '')
        elif gateway_result.success:
            status = CompensationStatus.APPLIED
            offset_applied = gateway_result.offset_applied
            accumulated_after = gateway_result.accumulated_after
            reason = gateway_result.reason
        elif gateway_result.decision in (OffsetDecision.REJECTED_LIMIT, OffsetDecision.REJECTED_BLOCKED):
            status = CompensationStatus.BLOCKED
            offset_applied = 0.0
            accumulated_after = gateway_result.accumulated_after
            reason = gateway_result.reason
        else:
            status = CompensationStatus.ERROR
            offset_applied = 0.0
            accumulated_after = gateway_result.accumulated_after if gateway_result else abs(assignment.accumulated_offset)
            reason = gateway_result.reason if gateway_result else 'Unknown error'
        
        CompensationEvent.objects.create(
            rule=rule,
            measurement_id=measurement_id,
            deviation_in=deviation,
            offset_calculated=calc_result['offset_calculated'],
            offset_applied=offset_applied,
            accumulated_before=abs(assignment.accumulated_offset) - abs(offset_applied) if gateway_result and gateway_result.success else abs(assignment.accumulated_offset),
            accumulated_after=accumulated_after,
            status=status.value if hasattr(status, 'value') else str(status),
            reason=reason[:200],  # Truncate to field max
        )


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_engine_instance: Optional[CompensationEngine] = None


def get_engine() -> CompensationEngine:
    """Get the singleton engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = CompensationEngine()
    return _engine_instance


def process_measurement(measurement) -> List[CompensationResult]:
    """
    Convenience function to process a measurement.
    
    Usage:
        from compensation.engine import process_measurement
        results = process_measurement(measurement)
    """
    engine = get_engine()
    return engine.process(measurement)