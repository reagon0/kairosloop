# dashboard/forms.py
"""
Forms for system setup configuration.
"""

from django import forms
from devices.models import Machine, GaugeConfig, ChannelConfig, ControllerConfig
from dmis.models import Feature, FeatureType, ToleranceMode


class MachineForm(forms.ModelForm):
    """Form for editing machine settings."""
    
    class Meta:
        model = Machine
        fields = ['name', 'description', 'location']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Tsugami Swiss #3'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Optional description'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Building A, Line 2'
            }),
        }


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


class ControllerConfigForm(forms.ModelForm):
    """Form for editing controller configuration."""
    
    class Meta:
        model = ControllerConfig
        fields = ['name', 'controller_type', 'host', 'port', 'active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Fanuc Main'
            }),
            'controller_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'host': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 192.168.1.100'
            }),
            'port': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 8193'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        help_texts = {
            'host': 'IP address for network-connected controllers',
            'port': 'Port number (FOCAS default: 8193)',
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
                'placeholder': 'e.g., A + B or (A - B) / 2'
            }),
            'tolerance_mode': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nominal': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
                'placeholder': '25.400'
            }),
            'tolerance_upper': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': 'any',
                'placeholder': '0.010'
            }),
            'tolerance_lower': forms.NumberInput(attrs={
                'class': 'form-input',
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
        help_texts = {
            'formula': 'Use inputs A, B, C... with operators: + - * / () abs() min() max()',
            'nominal': 'Target value (not used for TIR/Limit mode)',
            'tolerance_upper': 'Upper tolerance limit',
            'tolerance_lower': 'Lower tolerance limit (leave blank for symmetric)',
            'warning_percent': 'Warning at this % of tolerance (0-100)',
            'resolution': 'Decimal places (0-6)',
        }


class FeatureInputForm(forms.Form):
    """Form for a single feature input (A, B, C, ...)."""
    
    label = forms.CharField(
        max_length=2,
        widget=forms.TextInput(attrs={
            'class': 'form-input input-label',
            'readonly': 'readonly',
            'style': 'width: 50px; text-align: center; font-weight: 600;'
        })
    )
    channel_index = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, channels=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if channels:
            channel_choices = [('', '-- Select Channel --')]
            channel_choices += [
                (ch.channel_index, f"CH{ch.display_index}: {ch.name} ({ch.gauge.name})")
                for ch in channels
            ]
            self.fields['channel_index'].choices = channel_choices