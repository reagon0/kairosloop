# simulator/seed.py
"""
Seed data for testing the simulation.

Creates all required objects for a working simulation:
- GaugeConfig (N1700 gauge with 2 channels)
- Feature (OD Diameter with 2-probe average)
- ToolType (insert definition)
- ToolInstance (physical insert)
- ToolAssignment (loaded in machine)
- CompensationRule (links feature to tool assignment)

Usage:
    python manage.py shell
    >>> from simulator.seed import seed_all, validate, reset_all
    >>> seed_all()
    
    # Or just validate current state
    >>> validate()
    
    # Reset everything
    >>> reset_all()
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    message: str
    details: Optional[str] = None


def validate() -> List[ValidationResult]:
    """
    Validate that all required configuration exists for simulation.
    
    Returns list of validation results (pass/fail for each check).
    """
    results = []
    
    # 1. Check ControllerConfig exists
    from controller.models import ControllerConfig
    controller = ControllerConfig.objects.filter(protocol='TEST').first()
    if controller:
        results.append(ValidationResult(True, "Controller config exists", controller.name))
    else:
        results.append(ValidationResult(False, "No TEST controller found", "Run seed_all() to create"))
    
    # 2. Check GaugeConfig exists
    from measurement.models import GaugeConfig
    gauges = GaugeConfig.objects.filter(active=True)
    if gauges.exists():
        results.append(ValidationResult(True, f"{gauges.count()} Gauge(s) configured"))
    else:
        results.append(ValidationResult(False, "No Gauges configured", "Run seed_all() to create"))
    
    # 3. Check ToolType exists
    from tooling.models import ToolType
    tool_types = ToolType.objects.filter(active=True)
    if tool_types.exists():
        results.append(ValidationResult(True, f"{tool_types.count()} ToolType(s) defined", 
                                        ", ".join(t.name for t in tool_types[:3])))
    else:
        results.append(ValidationResult(False, "No ToolTypes defined", "Run seed_all() to create"))
    
    # 4. Check ToolInstance exists and is IN_USE
    from tooling.models import ToolInstance, InstanceStatus
    instances = ToolInstance.objects.filter(status=InstanceStatus.IN_USE)
    if instances.exists():
        results.append(ValidationResult(True, f"{instances.count()} ToolInstance(s) in use"))
    else:
        results.append(ValidationResult(False, "No ToolInstances in use", "Run seed_all() to create"))
    
    # 5. Check ToolAssignment exists and is active
    from tooling.models import ToolAssignment, AssignmentStatus
    assignments = ToolAssignment.objects.filter(
        status__in=[AssignmentStatus.ACTIVE, AssignmentStatus.WARNING, AssignmentStatus.CHANGE_REQUIRED]
    )
    if assignments.exists():
        for a in assignments:
            results.append(ValidationResult(
                True, 
                f"T{a.tool_position} assigned",
                f"{a.tool_instance.tool_type.name} @ {a.controller.name}"
            ))
    else:
        results.append(ValidationResult(False, "No active ToolAssignments", "Run seed_all() to create"))
    
    # 6. Check Feature exists
    from measurement.models import Feature
    features = Feature.objects.filter(active=True)
    if features.exists():
        results.append(ValidationResult(True, f"{features.count()} Feature(s) defined"))
    else:
        results.append(ValidationResult(False, "No Features defined", "Run seed_all() to create"))
    
    # 7. Check CompensationRule exists and has tool_assignment
    from compensation.models import CompensationRule
    rules = CompensationRule.objects.filter(active=True)
    if rules.exists():
        results.append(ValidationResult(True, f"{rules.count()} CompensationRule(s) linked"))
    else:
        results.append(ValidationResult(False, "No CompensationRules defined", "Run seed_all() to create"))
    
    return results


def print_validation():
    """Print validation results to console."""
    results = validate()
    
    print("\n" + "=" * 60)
    print("SIMULATION CONFIGURATION CHECK")
    print("=" * 60)
    
    all_valid = True
    for r in results:
        status = "✓" if r.valid else "✗"
        print(f"  {status} {r.message}")
        if r.details:
            print(f"      {r.details}")
        if not r.valid:
            all_valid = False
    
    print("=" * 60)
    if all_valid:
        print("✓ All checks passed - simulation ready!")
    else:
        print("✗ Some checks failed - run seed_all() to fix")
    print("=" * 60 + "\n")
    
    return all_valid


def is_valid() -> bool:
    """Quick check if simulation is ready to run."""
    results = validate()
    return all(r.valid for r in results)


def get_missing() -> List[str]:
    """Get list of missing configuration items."""
    results = validate()
    return [r.message for r in results if not r.valid]


def seed_all(force: bool = False):
    """
    Create all required seed data for simulation.
    
    Args:
        force: If True, reset and recreate everything
    """
    if force:
        reset_all()
    
    print("\nSeeding simulation data...")
    
    # =========================================================================
    # 1. Controller
    # =========================================================================
    from controller.models import ControllerConfig
    controller, created = ControllerConfig.objects.get_or_create(
        protocol='TEST',
        defaults={
            'name': 'Test CNC (Simulated)',
            'controller_type': 'test',
            'host': 'localhost',
            'port': 8193,
            'active': True,
        }
    )
    print(f"  {'Created' if created else 'Found'} controller: {controller.name}")
    
    # =========================================================================
    # 2. Gauge + Channels
    # =========================================================================
    from measurement.models import GaugeConfig, ChannelConfig
    
    gauge, created = GaugeConfig.objects.get_or_create(
        name='Marposs N1700',
        defaults={
            'driver_type': 'n1700',
            'filter_level': 5,
            'active': True,
        }
    )
    print(f"  {'Created' if created else 'Found'} gauge: {gauge.name}")
    
    # Create channels
    ch1, created = ChannelConfig.objects.get_or_create(
        gauge=gauge,
        channel_index=0,
        defaults={
            'name': 'OD Probe Left',
            'enabled': True,
        }
    )
    print(f"  {'Created' if created else 'Found'} channel: CH1 {ch1.name}")
    
    ch2, created = ChannelConfig.objects.get_or_create(
        gauge=gauge,
        channel_index=1,
        defaults={
            'name': 'OD Probe Right',
            'enabled': True,
        }
    )
    print(f"  {'Created' if created else 'Found'} channel: CH2 {ch2.name}")
    
    # =========================================================================
    # 3. ToolType
    # =========================================================================
    from tooling.models import ToolType
    tool_type, created = ToolType.objects.get_or_create(
        name='OD Roughing Insert',
        defaults={
            'manufacturer': 'Kennametal',
            'part_number': 'CNMG120408',
            'tool_kind': 'insert',
            'max_offset_distance': 0.1,
            'notes': 'Standard OD roughing insert for simulation',
        }
    )
    print(f"  {'Created' if created else 'Found'} tool type: {tool_type.name}")
    
    # =========================================================================
    # 4. ToolInstance
    # =========================================================================
    from tooling.models import ToolInstance, InstanceStatus
    instance = ToolInstance.objects.filter(
        tool_type=tool_type,
        status=InstanceStatus.IN_USE
    ).first()
    
    if not instance:
        instance = ToolInstance.objects.create(
            tool_type=tool_type,
            status=InstanceStatus.IN_USE,
        )
        print(f"  Created tool instance: {str(instance.uuid)[:8]}")
    else:
        print(f"  Found tool instance: {str(instance.uuid)[:8]}")
    
    # =========================================================================
    # 5. ToolAssignment
    # =========================================================================
    from tooling.models import ToolAssignment, AssignmentStatus
    assignment = ToolAssignment.objects.filter(
        controller=controller,
        tool_position=1,
        status__in=[AssignmentStatus.ACTIVE, AssignmentStatus.WARNING, AssignmentStatus.CHANGE_REQUIRED]
    ).first()
    
    if not assignment:
        assignment = ToolAssignment.objects.create(
            tool_instance=instance,
            controller=controller,
            tool_position=1,
            status=AssignmentStatus.ACTIVE,
        )
        print(f"  Created assignment: T1 @ {controller.name}")
    else:
        print(f"  Found assignment: T{assignment.tool_position} @ {controller.name}")
    
    # =========================================================================
    # 6. Feature + Inputs
    # =========================================================================
    from measurement.models import Feature, FeatureInput, FeatureType, ToleranceMode, Unit
    
    feature, created = Feature.objects.get_or_create(
        name='OD Diameter',
        defaults={
            'description': 'Outside diameter measured with 2 probes',
            'feature_type': FeatureType.DIAMETER,
            'formula': '(A + B) / 2',
            'tolerance_mode': ToleranceMode.BILATERAL,
            'nominal': 12.7,
            'tolerance_upper': 0.025,
            'tolerance_lower': 0.025,
            'warning_percent': 80,
            'unit': Unit.MM,
            'resolution': 4,
            'tool_type': tool_type,
            'active': True,
        }
    )
    print(f"  {'Created' if created else 'Found'} feature: {feature.name}")
    
    # Create feature inputs (A → CH0, B → CH1)
    input_a, created = FeatureInput.objects.get_or_create(
        feature=feature,
        label='A',
        defaults={'channel_index': 0}
    )
    print(f"  {'Created' if created else 'Found'} input: A → CH1")
    
    input_b, created = FeatureInput.objects.get_or_create(
        feature=feature,
        label='B',
        defaults={'channel_index': 1}
    )
    print(f"  {'Created' if created else 'Found'} input: B → CH2")
    
    # =========================================================================
    # 7. CompensationRule
    # =========================================================================
    from compensation.models import CompensationRule
    
    rule, created = CompensationRule.objects.get_or_create(
        feature=feature,
        tool_assignment=assignment,
        defaults={
            'offset_axis': 'X',
            'offset_direction': -1.0,
            'trigger_threshold': 0.005,
            'max_per_cycle': 0.010,
            'warning_threshold': 0.8,
            'active': True,
        }
    )
    print(f"  {'Created' if created else 'Found'} compensation rule: {feature.name} → T1")
    
    print("\nSeed complete!")
    print_validation()


def reset_all():
    """
    Reset all simulation data.
    
    WARNING: This deletes measurements, events, assignments, features, gauges!
    """
    print("\nResetting simulation data...")
    
    from measurement.models import Measurement, FeatureInput, Feature, ChannelConfig, GaugeConfig
    from compensation.models import CompensationEvent, CompensationRule
    from tooling.models import ToolAssignment, ToolInstance
    
    # Delete in order (respecting FK constraints)
    m_count = Measurement.objects.all().delete()[0]
    print(f"  Deleted {m_count} measurements")
    
    e_count = CompensationEvent.objects.all().delete()[0]
    print(f"  Deleted {e_count} compensation events")
    
    r_count = CompensationRule.objects.all().delete()[0]
    print(f"  Deleted {r_count} compensation rules")
    
    i_count = FeatureInput.objects.all().delete()[0]
    print(f"  Deleted {i_count} feature inputs")
    
    f_count = Feature.objects.all().delete()[0]
    print(f"  Deleted {f_count} features")
    
    c_count = ChannelConfig.objects.all().delete()[0]
    print(f"  Deleted {c_count} channels")
    
    g_count = GaugeConfig.objects.all().delete()[0]
    print(f"  Deleted {g_count} gauges")
    
    a_count = ToolAssignment.objects.all().delete()[0]
    print(f"  Deleted {a_count} tool assignments")
    
    ti_count = ToolInstance.objects.all().delete()[0]
    print(f"  Deleted {ti_count} tool instances")
    
    print("Reset complete!\n")


def reset_wear():
    """
    Reset just the wear tracking (keep config, clear runtime data).
    """
    from tooling.models import ToolAssignment, AssignmentStatus, ToolInstance
    from measurement.models import Measurement
    from compensation.models import CompensationEvent
    
    # Clear measurements and events
    Measurement.objects.all().delete()
    CompensationEvent.objects.all().delete()
    
    # Reset assignments
    ToolAssignment.objects.filter(
        status__in=[AssignmentStatus.ACTIVE, AssignmentStatus.WARNING, AssignmentStatus.CHANGE_REQUIRED]
    ).update(
        accumulated_offset=0.0,
        cycle_count=0,
        status=AssignmentStatus.ACTIVE
    )
    
    # Reset instances
    ToolInstance.objects.all().update(
        total_parts_cut=0,
        total_accumulated_wear=0.0
    )
    
    print("Wear tracking reset!")


# =============================================================================
# VALIDATION FOR OTHER MODULES
# =============================================================================

def get_validation_context() -> dict:
    """
    Get validation state for dashboard context.
    
    Returns dict with:
        - is_valid: bool
        - missing: list of missing items
        - warnings: list of warning messages
    """
    results = validate()
    
    missing = []
    warnings = []
    
    for r in results:
        if not r.valid:
            missing.append(r.message)
            if r.details:
                warnings.append(r.details)
    
    return {
        'is_valid': len(missing) == 0,
        'missing': missing,
        'warnings': warnings,
    }