# measurement/forms.py
"""
Forms for measurement configuration.
"""

from django import forms
from controller.models import Machine
from measurement.models import GaugeConfig, ChannelConfig
from measurement.models import Feature, FeatureType, ToleranceMode


class GaugeConfigForm(forms.ModelForm):
    """Form for editing gauge configuration."""
    
    class Meta:
        model = GaugeConfig
        fields = ['driver_type', 'name', 'filter_level', 'active']
        widgets = {
            'driver_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Main Gauge'
            }),
            'filter_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        help_texts = {
            'filter_level': 'Higher values = smoother but slower response',
        }


class ChannelConfigForm(forms.ModelForm):
    """Form for editing channel configuration."""
    
    class Meta:
        model = ChannelConfig
        fields = ['channel_index', 'name', 'enabled']
        widgets = {
            'channel_index': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., OD Probe Left'
            }),
            'enabled': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        help_texts = {
            'channel_index': '0-based index matching hardware (CH1 = index 0)',
        }


class FeatureForm(forms.ModelForm):
    """Form for editing measurement/feature configuration."""
    
    class Meta:
        model = Feature
        fields = [
            'name', 'feature_type', 'description',
            'formula',
            'tolerance_mode', 'nominal', 'tolerance_upper', 'tolerance_lower',
            'warning_percent', 'unit', 'resolution', 'active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Main OD'
            }),
            'feature_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Optional description'
            }),
            'formula': forms.TextInput(attrs={
                'class': 'form-input formula-input',
                'id': 'id_formula',
                'placeholder': 'e.g., A + B or (A - B) / 2'
            }),
            'tolerance_mode': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nominal': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_nominal',
                'step': 'any',
                'placeholder': '25.400'
            }),
            'tolerance_upper': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_tolerance_upper',
                'step': 'any',
                'placeholder': '0.010'
            }),
            'tolerance_lower': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_tolerance_lower',
                'step': 'any',
                'placeholder': '0.010'
            }),
            'warning_percent': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
                'min': 0,
                'max': 100,
                'placeholder': '80'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'resolution': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0,
                'max': 6
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
