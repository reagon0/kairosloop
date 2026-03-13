# dashboard/views.py
"""
Views for dashboard and system setup.
"""

import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from devices.models import Machine, GaugeConfig, ChannelConfig, ControllerConfig
from dmis.models import Feature, FeatureInput, FeatureType, ToleranceMode
from .forms import MachineForm, GaugeConfigForm, ChannelConfigForm, ControllerConfigForm, FeatureForm


def validate_formula_inputs(formula: str, defined_labels: list) -> str | None:
    """
    Validate that formula only references defined input labels.
    
    Returns error message if invalid, None if valid.
    """
    # Extract all letter sequences (potential input references)
    # Exclude known functions: ABS, MIN, MAX, SQRT
    known_functions = {'ABS', 'MIN', 'MAX', 'SQRT'}
    
    # Find all uppercase letter sequences
    potential_refs = re.findall(r'[A-Z]+', formula.upper())
    
    # Filter out known functions
    input_refs = [ref for ref in potential_refs if ref not in known_functions]
    
    # Check each reference exists in defined labels
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
# DASHBOARD
# =============================================================================

def dashboard(request):
    """Main live dashboard view."""
    import json
    
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
    
    # Get active gauge (first one for now, or from session/query param)
    selected_gauge_id = request.GET.get('gauge')
    if selected_gauge_id:
        selected_gauge = gauges.filter(id=selected_gauge_id).first()
    else:
        selected_gauge = gauges.first()
    
    context = {
        'machine': machine,
        'gauges': gauges,
        'selected_gauge': selected_gauge,
        'channels_json': json.dumps(channels_config),
        'filter_level': selected_gauge.filter_level if selected_gauge else 5,
    }
    return render(request, 'dashboard/dashboard.html', context)


# =============================================================================
# SYSTEM SETUP
# =============================================================================

def setup(request):
    """System setup page — machine, gauges, channels, controllers."""
    machine = Machine.get_or_create_default()
    
    context = {
        'machine': machine,
        'gauges': machine.gauges.prefetch_related('channels').all(),
        'controllers': machine.controllers.all(),
        'machine_form': MachineForm(instance=machine),
    }
    return render(request, 'dashboard/setup.html', context)


def setup_machine(request):
    """Edit machine settings."""
    machine = Machine.get_or_create_default()
    
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Machine settings saved.')
            return redirect('setup')
    else:
        form = MachineForm(instance=machine)
    
    return render(request, 'dashboard/setup_machine.html', {
        'form': form,
        'machine': machine,
    })


# =============================================================================
# GAUGE CONFIGURATION
# =============================================================================

def setup_gauge_add(request):
    """Add a new gauge configuration."""
    machine = Machine.get_or_create_default()
    
    if request.method == 'POST':
        form = GaugeConfigForm(request.POST)
        if form.is_valid():
            gauge = form.save(commit=False)
            gauge.machine = machine
            gauge.save()
            messages.success(request, f'Gauge "{gauge.name}" created.')
            return redirect('setup')
    else:
        form = GaugeConfigForm()
    
    return render(request, 'dashboard/setup_gauge_form.html', {
        'form': form,
        'is_new': True,
    })


def setup_gauge_edit(request, gauge_id):
    """Edit gauge configuration and channels."""
    gauge = get_object_or_404(GaugeConfig, id=gauge_id)
    
    if request.method == 'POST':
        form = GaugeConfigForm(request.POST, instance=gauge)
        if form.is_valid():
            form.save()
            messages.success(request, f'Gauge "{gauge.name}" updated.')
            return redirect('setup')
    else:
        form = GaugeConfigForm(instance=gauge)
    
    return render(request, 'dashboard/setup_gauge_form.html', {
        'form': form,
        'gauge': gauge,
        'channels': gauge.channels.order_by('channel_index'),
        'is_new': False,
    })


def setup_gauge_delete(request, gauge_id):
    """Delete a gauge configuration."""
    gauge = get_object_or_404(GaugeConfig, id=gauge_id)
    
    if request.method == 'POST':
        name = gauge.name
        gauge.delete()
        messages.success(request, f'Gauge "{name}" deleted.')
        return redirect('setup')
    
    return render(request, 'dashboard/setup_confirm_delete.html', {
        'object': gauge,
        'object_type': 'Gauge',
    })


# =============================================================================
# CHANNEL CONFIGURATION
# =============================================================================

def setup_channel_add(request, gauge_id):
    """Add a channel to a gauge."""
    gauge = get_object_or_404(GaugeConfig, id=gauge_id)
    
    # Find next available channel index
    existing_indices = list(gauge.channels.values_list('channel_index', flat=True))
    next_index = 0
    while next_index in existing_indices:
        next_index += 1
    
    if request.method == 'POST':
        form = ChannelConfigForm(request.POST)
        if form.is_valid():
            channel_index = form.cleaned_data['channel_index']
            # Check for duplicate
            if channel_index in existing_indices:
                form.add_error('channel_index', f'Channel index {channel_index} already exists on this gauge.')
            else:
                channel = form.save(commit=False)
                channel.gauge = gauge
                channel.save()
                messages.success(request, f'Channel "{channel.name}" added.')
                return redirect('setup_gauge_edit', gauge_id=gauge.id)
    else:
        form = ChannelConfigForm(initial={'channel_index': next_index})
    
    return render(request, 'dashboard/setup_channel_form.html', {
        'form': form,
        'gauge': gauge,
        'is_new': True,
    })


def setup_channel_edit(request, channel_id):
    """Edit a channel."""
    channel = get_object_or_404(ChannelConfig, id=channel_id)
    gauge = channel.gauge
    
    # Get existing indices, excluding current channel
    existing_indices = list(
        gauge.channels.exclude(id=channel.id).values_list('channel_index', flat=True)
    )
    
    if request.method == 'POST':
        form = ChannelConfigForm(request.POST, instance=channel)
        if form.is_valid():
            channel_index = form.cleaned_data['channel_index']
            # Check for duplicate (excluding self)
            if channel_index in existing_indices:
                form.add_error('channel_index', f'Channel index {channel_index} already exists on this gauge.')
            else:
                form.save()
                messages.success(request, f'Channel "{channel.name}" updated.')
                return redirect('setup_gauge_edit', gauge_id=gauge.id)
    else:
        form = ChannelConfigForm(instance=channel)
    
    return render(request, 'dashboard/setup_channel_form.html', {
        'form': form,
        'channel': channel,
        'gauge': gauge,
        'is_new': False,
    })


def setup_channel_delete(request, channel_id):
    """Delete a channel."""
    channel = get_object_or_404(ChannelConfig, id=channel_id)
    gauge_id = channel.gauge.id
    
    if request.method == 'POST':
        name = channel.name
        channel.delete()
        messages.success(request, f'Channel "{name}" deleted.')
        return redirect('setup_gauge_edit', gauge_id=gauge_id)
    
    return render(request, 'dashboard/setup_confirm_delete.html', {
        'object': channel,
        'object_type': 'Channel',
        'cancel_url': 'setup_gauge_edit',
        'cancel_id': gauge_id,
    })


# =============================================================================
# CONTROLLER CONFIGURATION
# =============================================================================

def setup_controller_add(request):
    """Add a new controller."""
    machine = Machine.get_or_create_default()
    
    if request.method == 'POST':
        form = ControllerConfigForm(request.POST)
        if form.is_valid():
            controller = form.save(commit=False)
            controller.machine = machine
            controller.save()
            messages.success(request, f'Controller "{controller.name}" created.')
            return redirect('setup')
    else:
        form = ControllerConfigForm()
    
    return render(request, 'dashboard/setup_controller_form.html', {
        'form': form,
        'is_new': True,
    })


def setup_controller_edit(request, controller_id):
    """Edit a controller."""
    controller = get_object_or_404(ControllerConfig, id=controller_id)
    
    if request.method == 'POST':
        form = ControllerConfigForm(request.POST, instance=controller)
        if form.is_valid():
            form.save()
            messages.success(request, f'Controller "{controller.name}" updated.')
            return redirect('setup')
    else:
        form = ControllerConfigForm(instance=controller)
    
    return render(request, 'dashboard/setup_controller_form.html', {
        'form': form,
        'controller': controller,
        'is_new': False,
    })


def setup_controller_delete(request, controller_id):
    """Delete a controller."""
    controller = get_object_or_404(ControllerConfig, id=controller_id)
    
    if request.method == 'POST':
        name = controller.name
        controller.delete()
        messages.success(request, f'Controller "{name}" deleted.')
        return redirect('setup')
    
    return render(request, 'dashboard/setup_confirm_delete.html', {
        'object': controller,
        'object_type': 'Controller',
    })


# =============================================================================
# MEASUREMENTS (Features)
# =============================================================================

def measurements(request):
    """List all measurements/features."""
    features = Feature.objects.filter(active=True).prefetch_related('inputs').order_by('name')
    
    # Build channel lookup map: channel_index -> {name, gauge_name}
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
    
    # Annotate each feature's inputs with channel info
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
    
    return render(request, 'dashboard/measurements.html', {
        'features': features,
    })


def measurement_add(request):
    """Add a new measurement/feature."""
    machine = Machine.get_or_create_default()
    channels = ChannelConfig.objects.filter(
        gauge__machine=machine,
        gauge__active=True,
        enabled=True
    ).select_related('gauge').order_by('gauge__name', 'channel_index')
    
    # Build channel choices for JS
    channel_choices = [
        {'index': ch.channel_index, 'label': f"CH{ch.display_index}: {ch.name} ({ch.gauge.name})"}
        for ch in channels
    ]
    
    if request.method == 'POST':
        form = FeatureForm(request.POST)
        
        # Parse inputs from POST
        input_count = int(request.POST.get('input_count', 0))
        input_labels = []
        inputs_data = []
        for i in range(input_count):
            label = request.POST.get(f'input_{i}_label')
            channel_idx = request.POST.get(f'input_{i}_channel')
            if label and channel_idx is not None and channel_idx != '':
                input_labels.append(label)
                inputs_data.append({'label': label, 'channel_index': int(channel_idx)})
        
        # Validate formula references only defined inputs
        formula = request.POST.get('formula', 'A').upper()
        formula_error = validate_formula_inputs(formula, input_labels)
        
        if form.is_valid() and not formula_error:
            feature = form.save()
            
            # Create inputs
            for inp in inputs_data:
                FeatureInput.objects.create(
                    feature=feature,
                    label=inp['label'],
                    channel_index=inp['channel_index']
                )
            
            messages.success(request, f'Measurement "{feature.name}" created.')
            return redirect('measurements')
        elif formula_error:
            form.add_error('formula', formula_error)
    else:
        form = FeatureForm()
        inputs_data = []
    
    import json
    return render(request, 'dashboard/measurement_form.html', {
        'form': form,
        'is_new': True,
        'channels_json': json.dumps(channel_choices),
        'inputs_json': json.dumps(inputs_data if request.method == 'POST' else []),
    })


def measurement_edit(request, feature_id):
    """Edit an existing measurement/feature."""
    feature = get_object_or_404(Feature, id=feature_id)
    machine = Machine.get_or_create_default()
    channels = ChannelConfig.objects.filter(
        gauge__machine=machine,
        gauge__active=True,
        enabled=True
    ).select_related('gauge').order_by('gauge__name', 'channel_index')
    
    # Build channel choices for JS
    channel_choices = [
        {'index': ch.channel_index, 'label': f"CH{ch.display_index}: {ch.name} ({ch.gauge.name})"}
        for ch in channels
    ]
    
    # Get existing inputs
    existing_inputs = [
        {'label': inp.label, 'channel_index': inp.channel_index}
        for inp in feature.inputs.order_by('label')
    ]
    
    if request.method == 'POST':
        form = FeatureForm(request.POST, instance=feature)
        
        # Parse inputs from POST
        input_count = int(request.POST.get('input_count', 0))
        input_labels = []
        inputs_data = []
        for i in range(input_count):
            label = request.POST.get(f'input_{i}_label')
            channel_idx = request.POST.get(f'input_{i}_channel')
            if label and channel_idx is not None and channel_idx != '':
                input_labels.append(label)
                inputs_data.append({'label': label, 'channel_index': int(channel_idx)})
        
        # Validate formula references only defined inputs
        formula = request.POST.get('formula', 'A').upper()
        formula_error = validate_formula_inputs(formula, input_labels)
        
        if form.is_valid() and not formula_error:
            feature = form.save()
            
            # Clear existing inputs and recreate
            feature.inputs.all().delete()
            
            # Create inputs
            for inp in inputs_data:
                FeatureInput.objects.create(
                    feature=feature,
                    label=inp['label'],
                    channel_index=inp['channel_index']
                )
            
            messages.success(request, f'Measurement "{feature.name}" updated.')
            return redirect('measurements')
        elif formula_error:
            form.add_error('formula', formula_error)
            existing_inputs = inputs_data  # Preserve user's input changes
    else:
        form = FeatureForm(instance=feature)
    
    import json
    return render(request, 'dashboard/measurement_form.html', {
        'form': form,
        'feature': feature,
        'is_new': False,
        'channels_json': json.dumps(channel_choices),
        'inputs_json': json.dumps(existing_inputs),
    })


def measurement_delete(request, feature_id):
    """Delete a measurement/feature."""
    feature = get_object_or_404(Feature, id=feature_id)
    
    if request.method == 'POST':
        name = feature.name
        feature.delete()
        messages.success(request, f'Measurement "{name}" deleted.')
        return redirect('measurements')
    
    return render(request, 'dashboard/setup_confirm_delete.html', {
        'object': feature,
        'object_type': 'Measurement',
        'cancel_url': 'measurements',
    })