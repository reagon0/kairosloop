# compensation/views.py
"""
Views for compensation configuration.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import CompensationRule, CompensationEvent
from .forms import CompensationRuleForm


def rule_list(request):
    """List all compensation rules."""
    rules = CompensationRule.objects.select_related(
        'feature', 'controller'
    ).order_by('feature__name', 'tool_number')
    
    return render(request, 'compensation/rule_list.html', {
        'rules': rules,
    })


def rule_add(request):
    """Add a new compensation rule."""
    if request.method == 'POST':
        form = CompensationRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            messages.success(request, f'Compensation rule for "{rule.feature.name}" created.')
            return redirect('compensation:rule_list')
    else:
        form = CompensationRuleForm()
    
    return render(request, 'compensation/rule_form.html', {
        'form': form,
        'is_new': True,
    })


def rule_edit(request, rule_id):
    """Edit a compensation rule."""
    rule = get_object_or_404(CompensationRule, id=rule_id)
    
    if request.method == 'POST':
        form = CompensationRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Compensation rule updated.')
            return redirect('compensation:rule_list')
    else:
        form = CompensationRuleForm(instance=rule)
    
    # Get recent events for this rule
    recent_events = rule.events.select_related('measurement')[:10]
    
    return render(request, 'compensation/rule_form.html', {
        'form': form,
        'rule': rule,
        'recent_events': recent_events,
        'is_new': False,
    })


def rule_delete(request, rule_id):
    """Delete a compensation rule."""
    rule = get_object_or_404(CompensationRule, id=rule_id)
    
    if request.method == 'POST':
        feature_name = rule.feature.name
        rule.delete()
        messages.success(request, f'Compensation rule for "{feature_name}" deleted.')
        return redirect('compensation:rule_list')
    
    return render(request, 'compensation/confirm_delete.html', {
        'object': rule,
        'object_type': 'Compensation Rule',
        'cancel_url': 'compensation:rule_list',
    })


@require_POST
def rule_reset(request, rule_id):
    """Reset accumulated offset for a rule."""
    rule = get_object_or_404(CompensationRule, id=rule_id)
    old_value = rule.accumulated_offset
    rule.reset_accumulated()
    messages.success(request, f'Reset accumulated offset from {old_value:+.4f} to 0.000')
    return redirect('compensation:rule_edit', rule_id=rule.id)


@require_POST
def rule_toggle(request, rule_id):
    """Toggle active state for a rule."""
    rule = get_object_or_404(CompensationRule, id=rule_id)
    rule.active = not rule.active
    rule.save(update_fields=['active', 'updated_at'])
    
    status = "enabled" if rule.active else "disabled"
    messages.success(request, f'Compensation rule {status}.')
    return redirect('compensation:rule_list')


def event_list(request):
    """List all compensation events."""
    events = CompensationEvent.objects.select_related(
        'rule__feature', 'rule__controller', 'measurement'
    ).order_by('-timestamp')[:100]
    
    return render(request, 'compensation/event_list.html', {
        'events': events,
    })


def rule_events(request, rule_id):
    """List events for a specific rule."""
    rule = get_object_or_404(CompensationRule, id=rule_id)
    events = rule.events.select_related('measurement').order_by('-timestamp')[:100]
    
    return render(request, 'compensation/event_list.html', {
        'rule': rule,
        'events': events,
    })
