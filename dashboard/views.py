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
    - Compensation status (tool wear gauges, recent events)
    - Statistics (pass/fail counts)
    """
    machine = Machine.get_or_create_default()
    
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
    
    # Get active compensation rules
    compensation_rules = CompensationRule.objects.filter(
        active=True
    ).select_related('feature', 'controller').order_by('feature__name')
    
    # Build compensation config
    compensation_config = []
    for rule in compensation_rules:
        compensation_config.append({
            'id': rule.id,
            'feature_name': rule.feature.name,
            'controller_name': rule.controller.name,
            'tool_number': rule.tool_number,
            'offset_register': rule.offset_register,
            'offset_axis': rule.offset_axis,
            'accumulated_offset': rule.accumulated_offset,
            'wear_limit': rule.wear_limit,
            'wear_percentage': rule.wear_percentage,
            'wear_status': rule.wear_status,
            'last_adjustment': rule.last_adjustment,
            'last_adjustment_at': rule.last_adjustment_at.isoformat() if rule.last_adjustment_at else None,
            'max_per_cycle': rule.max_per_cycle,
            'trigger_threshold': rule.trigger_threshold,
        })
    
    # Get recent compensation events
    recent_events = CompensationEvent.objects.select_related(
        'rule__feature', 'rule'
    ).order_by('-timestamp')[:15]
    
    events_list = [
        {
            'id': e.id,
            'feature_name': e.rule.feature.name,
            'tool_number': e.rule.tool_number,
            'offset_applied': e.offset_applied,
            'status': e.status,
            'reason': e.reason,
            'timestamp': e.timestamp.isoformat(),
            'accumulated_after': e.accumulated_after,
        }
        for e in recent_events
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
        'events_json': json.dumps(events_list),
        'stats_json': json.dumps(stats),
        
        # Settings
        'filter_level': selected_gauge.filter_level if selected_gauge else 5,
    }
    return render(request, 'dashboard/dashboard.html', context)
