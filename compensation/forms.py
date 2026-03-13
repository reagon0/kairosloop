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
            'feature', 'controller',
            'tool_number', 'offset_register', 'offset_axis', 'offset_direction',
            'trigger_mode', 'trigger_threshold', 'sample_count',
            'max_per_cycle', 'wear_limit', 'wear_limit_action',
            'active',
        ]
        widgets = {
            'feature': forms.Select(attrs={
                'class': 'form-select'
            }),
            'controller': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tool_number': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'placeholder': 'e.g., 1 for T01'
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
            'wear_limit': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
                'placeholder': '0.050'
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
        
        # Only show active features and controllers
        from measurement.models import Feature
        from controller.models import ControllerConfig
        
        self.fields['feature'].queryset = Feature.objects.filter(active=True).order_by('name')
        self.fields['controller'].queryset = ControllerConfig.objects.filter(active=True).order_by('name')
