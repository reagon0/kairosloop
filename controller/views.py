# controller/views.py
"""
Views for controller configuration.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Machine
from .models import ControllerConfig
from .forms import ControllerConfigForm


def controller_list(request):
    """List all controllers."""
    controllers = ControllerConfig.objects.order_by('name')
    
    return render(request, 'controller/controller_list.html', {
        'controllers': controllers,
    })


def controller_add(request):
    """Add a new controller."""
    machine = Machine.get_or_create_default()
    
    if request.method == 'POST':
        form = ControllerConfigForm(request.POST)
        if form.is_valid():
            controller = form.save(commit=False)
            controller.machine = machine
            controller.save()
            messages.success(request, f'Controller "{controller.name}" created.')
            return redirect('controller:controller_list')
    else:
        form = ControllerConfigForm()
    
    return render(request, 'controller/controller_form.html', {
        'form': form,
        'is_new': True,
    })


def controller_edit(request, controller_id):
    """Edit a controller."""
    controller = get_object_or_404(ControllerConfig, id=controller_id)
    
    if request.method == 'POST':
        form = ControllerConfigForm(request.POST, instance=controller)
        if form.is_valid():
            form.save()
            messages.success(request, f'Controller "{controller.name}" updated.')
            return redirect('controller:controller_list')
    else:
        form = ControllerConfigForm(instance=controller)
    
    return render(request, 'controller/controller_form.html', {
        'form': form,
        'controller': controller,
        'is_new': False,
    })


def controller_delete(request, controller_id):
    """Delete a controller."""
    controller = get_object_or_404(ControllerConfig, id=controller_id)
    
    if request.method == 'POST':
        name = controller.name
        controller.delete()
        messages.success(request, f'Controller "{name}" deleted.')
        return redirect('controller:controller_list')
    
    return render(request, 'controller/confirm_delete.html', {
        'object': controller,
        'object_type': 'Controller',
        'cancel_url': 'controller:controller_list',
    })


@require_POST
def controller_test(request, controller_id):
    """Test connection to controller."""
    controller = get_object_or_404(ControllerConfig, id=controller_id)
    
    # TODO: Implement actual connection test based on protocol
    # For now, just simulate
    if controller.protocol == 'TEST':
        controller.update_heartbeat()
        return JsonResponse({
            'success': True,
            'message': 'Test controller connected successfully'
        })
    
    if not controller.host:
        return JsonResponse({
            'success': False,
            'message': 'No host configured'
        })
    
    # Placeholder for actual connection test
    # This would use FOCAS2, MTConnect, etc. based on protocol
    try:
        # Simulate connection attempt
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(controller.timeout_ms / 1000)
        result = sock.connect_ex((controller.host, controller.port))
        sock.close()
        
        if result == 0:
            controller.update_heartbeat()
            return JsonResponse({
                'success': True,
                'message': f'Connected to {controller.host}:{controller.port}'
            })
        else:
            controller.set_error(f'Connection refused (error {result})')
            return JsonResponse({
                'success': False,
                'message': f'Connection refused to {controller.host}:{controller.port}'
            })
    except socket.timeout:
        controller.set_error('Connection timeout')
        return JsonResponse({
            'success': False,
            'message': f'Connection timeout to {controller.host}:{controller.port}'
        })
    except Exception as e:
        controller.set_error(str(e))
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
