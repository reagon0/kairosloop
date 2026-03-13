# dashboard/forms.py
"""
Forms for dashboard app.

Most forms have moved to their respective apps:
- measurement/forms.py: GaugeConfigForm, ChannelConfigForm, FeatureForm
- compensation/forms.py: CompensationRuleForm
- controller/forms.py: ControllerConfigForm

This file only contains MachineForm since Machine stays in devices app.
"""

from django import forms
from controller.models import Machine


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
