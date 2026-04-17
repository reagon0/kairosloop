# compensation/forms.py
"""
Forms for compensation configuration.
"""

from django import forms
from .models import CompensationRule


class CompensationRuleForm(forms.ModelForm):
    """Form for editing compensation rules."""
    
    class Meta:
        model = CompensationRule
        fields = [
            'feature', 'tool_assignment',
            'offset_register', 'offset_axis', 'offset_direction',
            'trigger_mode', 'trigger_threshold', 'sample_count',
            'max_per_cycle', 'warning_threshold', 'wear_limit_action',
            'active',
        ]
        widgets = {
            'feature': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tool_assignment': forms.Select(attrs={
                'class': 'form-select'
            }),
            'offset_register': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., D01 (optional)'
            }),
            'offset_axis': forms.Select(attrs={
                'class': 'form-select'
            }),
            'offset_direction': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
            }),
            'trigger_mode': forms.Select(attrs={
                'class': 'form-select'
            }),
            'trigger_threshold': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
                'placeholder': '0.005'
            }),
            'sample_count': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
            }),
            'max_per_cycle': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
                'placeholder': '0.010'
            }),
            'warning_threshold': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
                'min': 0,
                'max': 1,
                'placeholder': '0.8'
            }),
            'wear_limit_action': forms.Select(attrs={
                'class': 'form-select'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active features
        from measurement.models import Feature
        self.fields['feature'].queryset = Feature.objects.filter(active=True).order_by('name')
        
        # Only show active tool assignments (not replaced)
        from tooling.models import ToolAssignment, AssignmentStatus
        self.fields['tool_assignment'].queryset = ToolAssignment.objects.exclude(
            status=AssignmentStatus.REPLACED
        ).select_related(
            'tool_instance__tool_type', 'controller'
        ).order_by('controller__name', 'tool_position')