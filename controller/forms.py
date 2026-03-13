# controller/forms.py
"""
Forms for controller configuration.
"""

from django import forms
from .models import ControllerConfig, Protocol, OffsetMethod


class ControllerConfigForm(forms.ModelForm):
    """Form for editing controller configuration."""
    
    class Meta:
        model = ControllerConfig
        fields = [
            'name', 'controller_type', 'protocol',
            'host', 'port', 'timeout_ms',
            'signal_cycle_complete', 'signal_master_request', 
            'signal_part_present', 'signal_tool_change',
            'signal_ready', 'signal_alarm', 'signal_measuring',
            'signal_pass', 'signal_fail',
            'offset_method', 'offset_resolution', 'offset_write_delay_ms',
            'active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Tsugami B0205'
            }),
            'controller_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'protocol': forms.Select(attrs={
                'class': 'form-select'
            }),
            'host': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '192.168.1.100'
            }),
            'port': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '8193'
            }),
            'timeout_ms': forms.NumberInput(attrs={
                'class': 'form-input',
            }),
            # Inbound signals
            'signal_cycle_complete': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R100.0'
            }),
            'signal_master_request': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R100.1'
            }),
            'signal_part_present': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R100.2'
            }),
            'signal_tool_change': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R100.3'
            }),
            # Outbound signals
            'signal_ready': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R101.0'
            }),
            'signal_alarm': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R101.1'
            }),
            'signal_measuring': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R101.2'
            }),
            'signal_pass': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R101.3'
            }),
            'signal_fail': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'R101.4'
            }),
            # Offset settings
            'offset_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'offset_resolution': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any'
            }),
            'offset_write_delay_ms': forms.NumberInput(attrs={
                'class': 'form-input',
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
