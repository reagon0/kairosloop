# simulator/seed.py
"""
Seed data for testing the simulation.

Creates all required objects for a working simulation:
- ToolType (insert definition)
- ToolInstance (physical insert)
- ToolAssignment (loaded in machine)
- Links CompensationRule to the assignment

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
    
    # 2. Check ToolType exists
    from tooling.models import ToolType
    tool_types = ToolType.objects.filter(active=True)
    if tool_types.exists():
        results.append(ValidationResult(True, f"{tool_types.count()} ToolType(s) defined", 
                                        ", ".join(t.name for t in tool_types[:3])))
    else:
        results.append(ValidationResult(False, "No ToolTypes defined", "Run seed_all() to create"))
    
    # 3. Check ToolInstance exists and is IN_USE
    from tooling.models import ToolInstance, InstanceStatus
    instances = ToolInstance.objects.filter(status=InstanceStatus.IN_USE)
    if instances.exists():
        results.append(ValidationResult(True, f"{instances.count()} ToolInstance(s) in use"))
    else:
        results.append(ValidationResult(False, "No ToolInstances in use", "Run seed_all() to create"))
    
    # 4. Check ToolAssignment exists and is active
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
    
    # 5. Check Feature exists
    from measurement.models import Feature
    features = Feature.objects.filter(active=True)
    if features.exists():
        results.append(ValidationResult(True, f"{features.count()} Feature(s) defined"))
    else:
        results.append(ValidationResult(False, "No Features defined", "Create in /measurement/"))
    
    # 6. Check CompensationRule exists and has tool_assignment
    from compensation.models import CompensationRule
    rules = CompensationRule.objects.filter(active=True)
    if rules.exists():
        linked = rules.exclude(tool_assignment__isnull=True).count()
        unlinked = rules.filter(tool_assignment__isnull=True).count()
        if unlinked > 0:
            results.append(ValidationResult(
                False, 
                f"{unlinked} CompensationRule(s) missing tool_assignment",
                "Run seed_all() to link"
            ))
        else:
            results.append(ValidationResult(True, f"{linked} CompensationRule(s) linked"))
    else:
        results.append(ValidationResult(False, "No CompensationRules defined", "Create in /compensation/"))
    
    # 7. Check GaugeConfig exists
    from measurement.models import GaugeConfig
    gauges = GaugeConfig.objects.filter(active=True)
    if gauges.exists():
        results.append(ValidationResult(True, f"{gauges.count()} Gauge(s) configured"))
    else:
        results.append(ValidationResult(False, "No Gauges configured", "Create in /measurement/"))
    
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
    
    # 1. Ensure ControllerConfig exists
    from controller.models import ControllerConfig
    controller, created = ControllerConfig.objects.get_or_create(
        protocol='TEST',
        defaults={
            'name': 'Test CNC (Simulated)',
            'host': 'localhost',
            'port': 8193,
            'enabled': True,
        }
    )
    print(f"  {'Created' if created else 'Found'} controller: {controller.name}")
    
    # 2. Create ToolType
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
    
    # 3. Create ToolInstance (only if none in use)
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
        print(f"  Created tool instance: {instance.uuid}")
    else:
        print(f"  Found tool instance: {instance.uuid}")
    
    # 4. Create ToolAssignment (only if none active for T1)
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
    
    # 5. Link CompensationRules to assignment
    from compensation.models import CompensationRule
    unlinked_rules = CompensationRule.objects.filter(
        active=True,
        tool_assignment__isnull=True
    )
    
    if unlinked_rules.exists():
        updated = unlinked_rules.update(tool_assignment=assignment)
        print(f"  Linked {updated} compensation rule(s) to assignment")
    else:
        # Check if any rules exist
        rules = CompensationRule.objects.filter(active=True)
        if rules.exists():
            print(f"  {rules.count()} compensation rule(s) already linked")
        else:
            # Create a default rule if Feature exists
            from measurement.models import Feature
            feature = Feature.objects.filter(active=True).first()
            if feature:
                rule = CompensationRule.objects.create(
                    feature=feature,
                    tool_assignment=assignment,
                    offset_axis='X',
                    trigger_threshold=0.005,
                    max_per_cycle=0.010,
                    warning_threshold=0.8,
                    active=True,
                )
                print(f"  Created compensation rule for {feature.name}")
            else:
                print("  ⚠ No features found - create one first")
    
    print("\nSeed complete!")
    print_validation()


def reset_all():
    """
    Reset all simulation data.
    
    WARNING: This deletes measurements, events, and assignments!
    """
    print("\nResetting simulation data...")
    
    from measurement.models import Measurement
    from compensation.models import CompensationEvent
    from tooling.models import ToolAssignment, ToolInstance
    
    # Delete in order (respecting FK constraints)
    m_count = Measurement.objects.all().delete()[0]
    print(f"  Deleted {m_count} measurements")
    
    e_count = CompensationEvent.objects.all().delete()[0]
    print(f"  Deleted {e_count} compensation events")
    
    a_count = ToolAssignment.objects.all().delete()[0]
    print(f"  Deleted {a_count} tool assignments")
    
    i_count = ToolInstance.objects.all().delete()[0]
    print(f"  Deleted {i_count} tool instances")
    
    print("Reset complete!\n")


def reset_wear():
    """
    Reset just the wear tracking (keep assignments, clear accumulated offset).
    """
    from tooling.models import ToolAssignment, AssignmentStatus
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