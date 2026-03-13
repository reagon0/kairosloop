# measurement/views.py
"""
Views for measurement configuration.

Handles: Features (measurements), Gauges, Channels
"""

import re
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from measurement.models import Feature, FeatureInput
from .forms import GaugeConfigForm, ChannelConfigForm, FeatureForm
from controller.models import Machine
from measurement.models import GaugeConfig, ChannelConfig


def validate_formula_inputs(formula: str, defined_labels: list) -> str | None:
    """
    Validate that formula only references defined input labels.
    
    Returns error message if invalid, None if valid.
    """
    known_functions = {'ABS', 'MIN', 'MAX', 'SQRT'}
    potential_refs = re.findall(r'[A-Z]+', formula.upper())
    input_refs = [ref for ref in potential_refs if ref not in known_functions]
    defined_set = set(label.upper() for label in defined_labels)
    missing = [ref for ref in input_refs if ref not in defined_set]
    
    if missing:
        missing_unique = sorted(set(missing))
        if len(missing_unique) == 1:
            return f"Formula references undefined input '{missing_unique[0]}'. Add it in the Inputs section."
        else:
            return f"Formula references undefined inputs: {', '.join(missing_unique)}. Add them in the Inputs section."
    
    return None


# =============================================================================
# FEATURES (Measurements)
# =============================================================================

def feature_list(request):
    """List all features/measurements."""
    features = Feature.objects.filter(active=True).prefetch_related('inputs').order_by('name')
    
    machine = Machine.get_or_create_default()
    channels = ChannelConfig.objects.filter(
        gauge__machine=machine,
        enabled=True
    ).select_related('gauge')
    
    channel_map = {
        ch.channel_index: {
            'name': ch.name,
            'gauge': ch.gauge.name,
            'display': f"{ch.name} ({ch.gauge.name})"
        }
        for ch in channels
    }
    
    for feature in features:
        feature.resolved_inputs = []
        for inp in feature.inputs.all():
            ch_info = channel_map.get(inp.channel_index)
            feature.resolved_inputs.append({
                'label': inp.label,
                'channel_index': inp.channel_index,
                'channel_name': ch_info['name'] if ch_info else f"CH{inp.channel_index + 1}",
                'gauge_name': ch_info['gauge'] if ch_info else "Unknown",
                'display': ch_info['display'] if ch_info else f"CH{inp.channel_index + 1}",
            })
    
    return render(request, 'measurement/feature_list.html', {
        'features': features,
    })


def feature_add(request):
    """Add a new feature/measurement."""
    machine = Machine.get_or_create_default()
    channels = ChannelConfig.objects.filter(
        gauge__machine=machine,
        gauge__active=True,
        enabled=True
    ).select_related('gauge').order_by('gauge__name', 'channel_index')
    
    channel_choices = [
        {'index': ch.channel_index, 'label': f"CH{ch.display_index}: {ch.name} ({ch.gauge.name})"}
        for ch in channels
    ]
    
    if request.method == 'POST':
        form = FeatureForm(request.POST)
        
        input_count = int(request.POST.get('input_count', 0))
        input_labels = []
        inputs_data = []
        for i in range(input_count):
            label = request.POST.get(f'input_{i}_label')
            channel_idx = request.POST.get(f'input_{i}_channel')
            if label and channel_idx is not None and channel_idx != '':
                input_labels.append(label)
                inputs_data.append({'label': label, 'channel_index': int(channel_idx)})
        
        formula = request.POST.get('formula', 'A').upper()
        formula_error = validate_formula_inputs(formula, input_labels)
        
        if form.is_valid() and not formula_error:
            feature = form.save()
            
            for inp in inputs_data:
                FeatureInput.objects.create(
                    feature=feature,
                    label=inp['label'],
                    channel_index=inp['channel_index']
                )
            
            messages.success(request, f'Measurement "{feature.name}" created.')
            return redirect('measurement:feature_list')
        elif formula_error:
            form.add_error('formula', formula_error)
    else:
        form = FeatureForm()
        inputs_data = []
    
    return render(request, 'measurement/feature_form.html', {
        'form': form,
        'is_new': True,
        'channels_json': json.dumps(channel_choices),
        'inputs_json': json.dumps(inputs_data if request.method == 'POST' else []),
    })


def feature_edit(request, feature_id):
    """Edit an existing feature/measurement."""
    feature = get_object_or_404(Feature, id=feature_id)
    machine = Machine.get_or_create_default()
    channels = ChannelConfig.objects.filter(
        gauge__machine=machine,
        gauge__active=True,
        enabled=True
    ).select_related('gauge').order_by('gauge__name', 'channel_index')
    
    channel_choices = [
        {'index': ch.channel_index, 'label': f"CH{ch.display_index}: {ch.name} ({ch.gauge.name})"}
        for ch in channels
    ]
    
    existing_inputs = [
        {'label': inp.label, 'channel_index': inp.channel_index}
        for inp in feature.inputs.order_by('label')
    ]
    
    if request.method == 'POST':
        form = FeatureForm(request.POST, instance=feature)
        
        input_count = int(request.POST.get('input_count', 0))
        input_labels = []
        inputs_data = []
        for i in range(input_count):
            label = request.POST.get(f'input_{i}_label')
            channel_idx = request.POST.get(f'input_{i}_channel')
            if label and channel_idx is not None and channel_idx != '':
                input_labels.append(label)
                inputs_data.append({'label': label, 'channel_index': int(channel_idx)})
        
        formula = request.POST.get('formula', 'A').upper()
        formula_error = validate_formula_inputs(formula, input_labels)
        
        if form.is_valid() and not formula_error:
            feature = form.save()
            feature.inputs.all().delete()
            
            for inp in inputs_data:
                FeatureInput.objects.create(
                    feature=feature,
                    label=inp['label'],
                    channel_index=inp['channel_index']
                )
            
            messages.success(request, f'Measurement "{feature.name}" updated.')
            return redirect('measurement:feature_list')
        elif formula_error:
            form.add_error('formula', formula_error)
            existing_inputs = inputs_data
    else:
        form = FeatureForm(instance=feature)
    
    return render(request, 'measurement/feature_form.html', {
        'form': form,
        'feature': feature,
        'is_new': False,
        'channels_json': json.dumps(channel_choices),
        'inputs_json': json.dumps(existing_inputs),
    })


def feature_delete(request, feature_id):
    """Delete a feature/measurement."""
    feature = get_object_or_404(Feature, id=feature_id)
    
    if request.method == 'POST':
        name = feature.name
        feature.delete()
        messages.success(request, f'Measurement "{name}" deleted.')
        return redirect('measurement:feature_list')
    
    return render(request, 'measurement/confirm_delete.html', {
        'object': feature,
        'object_type': 'Measurement',
        'cancel_url': 'measurement:feature_list',
    })


# =============================================================================
# GAUGES
# =============================================================================

def gauge_list(request):
    """List all gauges."""
    machine = Machine.get_or_create_default()
    gauges = machine.gauges.prefetch_related('channels').all()
    
    return render(request, 'measurement/gauge_list.html', {
        'gauges': gauges,
        'machine': machine,
    })


def gauge_add(request):
    """Add a new gauge."""
    machine = Machine.get_or_create_default()
    
    if request.method == 'POST':
        form = GaugeConfigForm(request.POST)
        if form.is_valid():
            gauge = form.save(commit=False)
            gauge.machine = machine
            gauge.save()
            messages.success(request, f'Gauge "{gauge.name}" created.')
            return redirect('measurement:gauge_list')
    else:
        form = GaugeConfigForm()
    
    return render(request, 'measurement/gauge_form.html', {
        'form': form,
        'is_new': True,
    })


def gauge_edit(request, gauge_id):
    """Edit gauge configuration and view channels."""
    gauge = get_object_or_404(GaugeConfig, id=gauge_id)
    
    if request.method == 'POST':
        form = GaugeConfigForm(request.POST, instance=gauge)
        if form.is_valid():
            form.save()
            messages.success(request, f'Gauge "{gauge.name}" updated.')
            return redirect('measurement:gauge_list')
    else:
        form = GaugeConfigForm(instance=gauge)
    
    return render(request, 'measurement/gauge_form.html', {
        'form': form,
        'gauge': gauge,
        'channels': gauge.channels.order_by('channel_index'),
        'is_new': False,
    })


def gauge_delete(request, gauge_id):
    """Delete a gauge."""
    gauge = get_object_or_404(GaugeConfig, id=gauge_id)
    
    if request.method == 'POST':
        name = gauge.name
        gauge.delete()
        messages.success(request, f'Gauge "{name}" deleted.')
        return redirect('measurement:gauge_list')
    
    return render(request, 'measurement/confirm_delete.html', {
        'object': gauge,
        'object_type': 'Gauge',
        'cancel_url': 'measurement:gauge_list',
    })


# =============================================================================
# CHANNELS
# =============================================================================

def channel_add(request, gauge_id):
    """Add a channel to a gauge."""
    gauge = get_object_or_404(GaugeConfig, id=gauge_id)
    
    existing_indices = list(gauge.channels.values_list('channel_index', flat=True))
    next_index = 0
    while next_index in existing_indices:
        next_index += 1
    
    if request.method == 'POST':
        form = ChannelConfigForm(request.POST)
        if form.is_valid():
            channel_index = form.cleaned_data['channel_index']
            if channel_index in existing_indices:
                form.add_error('channel_index', f'Channel index {channel_index} already exists on this gauge.')
            else:
                channel = form.save(commit=False)
                channel.gauge = gauge
                channel.save()
                messages.success(request, f'Channel "{channel.name}" added.')
                return redirect('measurement:gauge_edit', gauge_id=gauge.id)
    else:
        form = ChannelConfigForm(initial={'channel_index': next_index})
    
    return render(request, 'measurement/channel_form.html', {
        'form': form,
        'gauge': gauge,
        'is_new': True,
    })


def channel_edit(request, channel_id):
    """Edit a channel."""
    channel = get_object_or_404(ChannelConfig, id=channel_id)
    gauge = channel.gauge
    
    existing_indices = list(
        gauge.channels.exclude(id=channel.id).values_list('channel_index', flat=True)
    )
    
    if request.method == 'POST':
        form = ChannelConfigForm(request.POST, instance=channel)
        if form.is_valid():
            channel_index = form.cleaned_data['channel_index']
            if channel_index in existing_indices:
                form.add_error('channel_index', f'Channel index {channel_index} already exists on this gauge.')
            else:
                form.save()
                messages.success(request, f'Channel "{channel.name}" updated.')
                return redirect('measurement:gauge_edit', gauge_id=gauge.id)
    else:
        form = ChannelConfigForm(instance=channel)
    
    return render(request, 'measurement/channel_form.html', {
        'form': form,
        'channel': channel,
        'gauge': gauge,
        'is_new': False,
    })


def channel_delete(request, channel_id):
    """Delete a channel."""
    channel = get_object_or_404(ChannelConfig, id=channel_id)
    gauge_id = channel.gauge.id
    
    if request.method == 'POST':
        name = channel.name
        channel.delete()
        messages.success(request, f'Channel "{name}" deleted.')
        return redirect('measurement:gauge_edit', gauge_id=gauge_id)
    
    return render(request, 'measurement/confirm_delete.html', {
        'object': channel,
        'object_type': 'Channel',
        'cancel_url': 'measurement:gauge_edit',
        'cancel_id': gauge_id,
    })
