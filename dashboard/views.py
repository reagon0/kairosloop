# dashboard/views.py
"""
Views for live operator dashboard.

This is the main runtime view where operators monitor measurements,
see live gauge values, and observe compensation status.
"""

import json
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from measurement.models import Feature, Measurement, GaugeConfig, ChannelConfig
from compensation.models import CompensationRule, CompensationEvent
from controller.models import Machine


def dashboard(request):
    """
    Main live dashboard view.
    
    Shows:
    - Live channel values from gauges
    - Feature calculations with tolerance status & sparklines
    - Tool assignments with wear/usage status
    - Recent compensation events
    - Statistics (pass/fail counts)
    """
    machine = Machine.get_or_create_default()
    
    # Get validation state
    config_valid = True
    config_warnings = []
    try:
        from simulator.seed import get_validation_context
        validation = get_validation_context()
        config_valid = validation['is_valid']
        config_warnings = validation['missing']
    except Exception:
        pass
    
    # Get all active gauges with their channels
    gauges = GaugeConfig.objects.filter(
        machine=machine, 
        active=True
    ).prefetch_related('channels')
    
    # Build channel config for JS
    channels_config = []
    for gauge in gauges:
        for channel in gauge.channels.filter(enabled=True).order_by('channel_index'):
            channels_config.append({
                'id': channel.id,
                'gauge_id': gauge.id,
                'gauge_name': gauge.name,
                'channel_index': channel.channel_index,
                'name': channel.name,
                'display_name': f"CH{channel.display_index}: {channel.name}",
            })
    
    # Get active gauge
    selected_gauge_id = request.GET.get('gauge')
    if selected_gauge_id:
        selected_gauge = gauges.filter(id=selected_gauge_id).first()
    else:
        selected_gauge = gauges.first()
    
    # Get active features with their inputs
    features = Feature.objects.filter(
        active=True
    ).prefetch_related('inputs').order_by('name')
    
    # Build feature config for JS (includes sparkline data)
    features_config = []
    for feature in features:
        inputs = []
        for inp in feature.inputs.all():
            inputs.append({
                'label': inp.label,
                'channel_index': inp.channel_index,
            })
        
        # Get last 20 measurements for sparkline
        recent_measurements = Measurement.objects.filter(
            feature=feature
        ).order_by('-timestamp')[:20]
        
        sparkline_data = [
            {
                'value': m.computed_value,
                'deviation': m.deviation,
                'status': m.status,
                'timestamp': m.timestamp.isoformat(),
            }
            for m in reversed(recent_measurements)
        ]
        
        # Get last measurement for initial display
        last_measurement = recent_measurements.first() if recent_measurements else None
        
        features_config.append({
            'id': feature.id,
            'name': feature.name,
            'formula': feature.formula,
            'inputs': inputs,
            'nominal': feature.nominal,
            'tolerance_upper': feature.tolerance_upper,
            'tolerance_lower': feature.tolerance_lower,
            'tolerance_mode': feature.tolerance_mode,
            'unit': feature.unit,
            'resolution': feature.resolution,
            'sparkline': sparkline_data,
            'last_value': last_measurement.computed_value if last_measurement else None,
            'last_status': last_measurement.status if last_measurement else None,
            'last_deviation': last_measurement.deviation if last_measurement else None,
        })
    
    # Get active tool assignments (NEW - replaces compensation rules for wear display)
    tool_assignments_config = []
    try:
        from tooling.models import ToolAssignment, AssignmentStatus
        
        tool_assignments = ToolAssignment.objects.filter(
            status__in=[AssignmentStatus.ACTIVE, AssignmentStatus.WARNING, AssignmentStatus.CHANGE_REQUIRED]
        ).select_related('tool_instance', 'tool_instance__tool_type', 'controller')
        
        for assignment in tool_assignments:
            tool_type = assignment.tool_instance.tool_type
            tool_assignments_config.append({
                'id': assignment.id,
                'uuid': str(assignment.uuid),
                'tool_position': assignment.tool_position,
                'tool_name': tool_type.name,
                'controller_name': assignment.controller.name,
                'accumulated_offset': assignment.accumulated_offset,
                'usage_percentage': assignment.usage_percentage,
                'max_offset': tool_type.max_offset_distance,
                'status': assignment.status,
                'installed_at': assignment.installed_at.isoformat(),
                'cycle_count': assignment.cycle_count,
            })
    except Exception:
        # Tooling app may not be migrated yet
        pass
    
    # Get active compensation rules (for trigger threshold info)
    compensation_rules = CompensationRule.objects.filter(
        active=True
    ).select_related('feature', 'tool_assignment', 'tool_assignment__tool_instance', 'tool_assignment__tool_instance__tool_type')
    
    # Build compensation config
    compensation_config = []
    for rule in compensation_rules:
        if rule.tool_assignment:
            assignment = rule.tool_assignment
            tool_type = assignment.tool_instance.tool_type
            compensation_config.append({
                'id': rule.id,
                'feature_name': rule.feature.name,
                'tool_assignment_id': assignment.id,
                'tool_position': assignment.tool_position,
                'tool_name': tool_type.name,
                'controller_name': assignment.controller.name,
                'offset_axis': rule.offset_axis,
                'trigger_threshold': rule.trigger_threshold,
                'max_per_cycle': rule.max_per_cycle,
                'warning_threshold': rule.warning_threshold,
                # From tool assignment
                'accumulated_offset': assignment.accumulated_offset,
                'max_offset': tool_type.max_offset_distance,
                'usage_percentage': assignment.usage_percentage,
                'status': assignment.status,
            })
        else:
            # Legacy support
            compensation_config.append({
                'id': rule.id,
                'feature_name': rule.feature.name,
                'tool_assignment_id': None,
                'tool_position': rule.tool_number,
                'tool_name': f'T{rule.tool_number}',
                'controller_name': rule.controller.name if rule.controller else 'Unknown',
                'offset_axis': rule.offset_axis,
                'trigger_threshold': rule.trigger_threshold,
                'max_per_cycle': rule.max_per_cycle,
                'warning_threshold': rule.warning_threshold,
                'accumulated_offset': rule.accumulated_offset or 0,
                'max_offset': rule.wear_limit or 0.1,
                'usage_percentage': rule.wear_percentage,
                'status': rule.wear_status,
            })
    
    # Get recent compensation events
    recent_events = CompensationEvent.objects.select_related(
        'rule__feature', 'rule', 'rule__tool_assignment', 'rule__tool_assignment__tool_instance'
    ).order_by('-timestamp')[:15]
    
    events_list = []
    for e in recent_events:
        tool_pos = e.rule.effective_tool_position
        events_list.append({
            'id': e.id,
            'feature_name': e.rule.feature.name,
            'tool_number': tool_pos,
            'offset_applied': e.offset_applied,
            'status': e.status,
            'reason': e.reason,
            'timestamp': e.timestamp.isoformat(),
            'accumulated_after': e.accumulated_after,
        })
    
    # Build trend data for chart (last 50 measurements per feature)
    trend_data = {}
    for feature in features:
        measurements = Measurement.objects.filter(
            feature=feature
        ).order_by('-timestamp')[:50]
        
        # Get compensation events for these measurements
        measurement_ids = [m.id for m in measurements]
        comp_events = CompensationEvent.objects.filter(
            measurement_id__in=measurement_ids
        ).select_related('rule')
        
        # Map measurement_id to offset
        offset_map = {}
        for ce in comp_events:
            if ce.measurement_id:
                offset_map[ce.measurement_id] = {
                    'offset': ce.offset_applied,
                    'status': ce.status,
                }
        
        trend_data[feature.id] = [
            {
                'timestamp': m.timestamp.isoformat(),
                'deviation': m.deviation,
                'status': m.status,
                'offset': offset_map.get(m.id, {}).get('offset'),
                'offset_status': offset_map.get(m.id, {}).get('status'),
            }
            for m in reversed(measurements)
        ]
    
    # Calculate stats (today)
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_measurements = Measurement.objects.filter(timestamp__gte=today_start)
    
    stats = {
        'total_today': today_measurements.count(),
        'pass_today': today_measurements.filter(status='OK').count(),
        'warn_today': today_measurements.filter(status='WARN').count(),
        'fail_today': today_measurements.filter(status='ALARM').count(),
        'total_all': Measurement.objects.count(),
    }
    
    # Calculate pass rate
    if stats['total_today'] > 0:
        stats['pass_rate'] = round(stats['pass_today'] / stats['total_today'] * 100, 1)
    else:
        stats['pass_rate'] = 0
    
    context = {
        'machine': machine,
        'gauges': gauges,
        'selected_gauge': selected_gauge,
        'features': features,
        'compensation_rules': compensation_rules,
        'recent_events': recent_events,
        'stats': stats,
        
        # JSON for JavaScript
        'channels_json': json.dumps(channels_config),
        'features_json': json.dumps(features_config),
        'compensation_json': json.dumps(compensation_config),
        'tool_assignments_json': json.dumps(tool_assignments_config),
        'events_json': json.dumps(events_list),
        'stats_json': json.dumps(stats),
        'trend_data_json': json.dumps(trend_data),
        
        # Settings
        'filter_level': selected_gauge.filter_level if selected_gauge else 5,
        
        # Validation
        'config_valid': config_valid,
        'config_warnings': config_warnings,
    }
    return render(request, 'dashboard/dashboard.html', context)

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
 
from controller.models import ControllerConfig, Machine
from measurement.models import GaugeConfig, ChannelConfig, Feature, FeatureInput
from compensation.models import CompensationRule
from tooling.models import ToolType, ToolInstance, ToolAssignment, AssignmentStatus
 
 
def setup(request):
    """Main setup page showing full configuration hierarchy."""
    
    # =========================================================================
    # MACHINE & CONTROLLER
    # =========================================================================
    machines = Machine.objects.all()
    controllers = ControllerConfig.objects.select_related('machine').all()
    
    # =========================================================================
    # GAUGE & CHANNELS
    # =========================================================================
    gauges = GaugeConfig.objects.prefetch_related('channels').all()
    
    # =========================================================================
    # FEATURES
    # =========================================================================
    features = Feature.objects.prefetch_related(
    'inputs'
    ).all().order_by('-active', 'name')
    
    # =========================================================================
    # TOOL TYPES, INSTANCES & ASSIGNMENTS
    # =========================================================================
    tool_types = ToolType.objects.filter(active=True)
    
    tool_assignments = ToolAssignment.objects.select_related(
        'tool_instance__tool_type',
        'controller'
    ).exclude(status=AssignmentStatus.REPLACED).order_by('tool_position')
    
    # =========================================================================
    # COMPENSATION RULES
    # =========================================================================
    compensation_rules = CompensationRule.objects.select_related(
        'feature',
        'tool_assignment__tool_instance__tool_type',
        'tool_assignment__controller'
    ).all().order_by('-active', 'feature__name')
    
    # =========================================================================
    # VALIDATION WARNINGS
    # =========================================================================
    warnings = []
    
    # Check for features without compensation rules
    features_with_rules = set(
        CompensationRule.objects.filter(active=True).values_list('feature_id', flat=True)
    )
    for feature in features:
        if feature.active and feature.id not in features_with_rules:
            warnings.append({
                'level': 'warning',
                'category': 'feature',
                'item': feature.name,
                'message': f'Feature "{feature.name}" has no active compensation rule'
            })
    
    # Check for compensation rules without tool assignments
    for rule in compensation_rules:
        if rule.active and not rule.tool_assignment:
            warnings.append({
                'level': 'warning', 
                'category': 'compensation',
                'item': rule.feature.name,
                'message': f'Compensation rule for "{rule.feature.name}" has no tool assignment'
            })
    
    # Check for no active controller
    active_controllers = [c for c in controllers if c.active]
    if not active_controllers:
        warnings.append({
            'level': 'error',
            'category': 'controller',
            'item': 'Controller',
            'message': 'No active controller configured'
        })
    
    # Check for no active gauge
    active_gauges = [g for g in gauges if g.active]
    if not active_gauges:
        warnings.append({
            'level': 'error',
            'category': 'gauge',
            'item': 'Gauge',
            'message': 'No active gauge configured'
        })
    
    # Check for no active features
    active_features = [f for f in features if f.active]
    if not active_features:
        warnings.append({
            'level': 'error',
            'category': 'feature',
            'item': 'Feature',
            'message': 'No active features configured'
        })
    
    # Check for features without channel inputs
    for feature in features:
        if feature.active and not feature.inputs.exists():
            warnings.append({
                'level': 'error',
                'category': 'feature',
                'item': feature.name,
                'message': f'Feature "{feature.name}" has no channel inputs'
            })
    
    # Check for tool assignments approaching limit
    for assignment in tool_assignments:
        if assignment.status == AssignmentStatus.WARNING:
            warnings.append({
                'level': 'warning',
                'category': 'tool',
                'item': f'T{assignment.tool_position}',
                'message': f'Tool T{assignment.tool_position} approaching wear limit'
            })
        elif assignment.status == AssignmentStatus.CHANGE_REQUIRED:
            warnings.append({
                'level': 'error',
                'category': 'tool',
                'item': f'T{assignment.tool_position}',
                'message': f'Tool T{assignment.tool_position} requires change'
            })
    
    context = {
        'machines': machines,
        'controllers': controllers,
        'gauges': gauges,
        'features': features,
        'tool_types': tool_types,
        'tool_assignments': tool_assignments,
        'compensation_rules': compensation_rules,
        'warnings': warnings,
        'error_count': len([w for w in warnings if w['level'] == 'error']),
        'warning_count': len([w for w in warnings if w['level'] == 'warning']),
    }
    
    return render(request, 'dashboard/setup.html', context)
 
 
@require_POST
def toggle_feature(request, feature_id):
    """Toggle feature active state via AJAX."""
    try:
        feature = Feature.objects.get(id=feature_id)
        feature.active = not feature.active
        feature.save()
        return JsonResponse({
            'success': True,
            'active': feature.active,
            'message': f'Feature "{feature.name}" {"activated" if feature.active else "deactivated"}'
        })
    except Feature.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Feature not found'}, status=404)
 
 
@require_POST
def toggle_compensation_rule(request, rule_id):
    """Toggle compensation rule active state via AJAX."""
    try:
        rule = CompensationRule.objects.get(id=rule_id)
        rule.active = not rule.active
        rule.save()
        return JsonResponse({
            'success': True,
            'active': rule.active,
            'message': f'Compensation rule {"enabled" if rule.active else "disabled"}'
        })
    except CompensationRule.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Rule not found'}, status=404)
 
 
@require_POST
def toggle_controller(request, controller_id):
    """Toggle controller active state via AJAX."""
    try:
        controller = ControllerConfig.objects.get(id=controller_id)
        controller.active = not controller.active
        controller.save()
        return JsonResponse({
            'success': True,
            'active': controller.active,
            'message': f'Controller "{controller.name}" {"activated" if controller.active else "deactivated"}'
        })
    except ControllerConfig.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Controller not found'}, status=404)
 
 
@require_POST
def toggle_gauge(request, gauge_id):
    """Toggle gauge active state via AJAX."""
    try:
        gauge = GaugeConfig.objects.get(id=gauge_id)
        gauge.active = not gauge.active
        gauge.save()
        return JsonResponse({
            'success': True,
            'active': gauge.active,
            'message': f'Gauge "{gauge.name}" {"activated" if gauge.active else "deactivated"}'
        })
    except GaugeConfig.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Gauge not found'}, status=404)
 