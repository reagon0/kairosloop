# dashboard/urls.py
"""
URL routing for dashboard app.

Dashboard is now ONLY the live operator view.
Configuration has moved to:
- /measurement/ - Gauges, channels, features
- /compensation/ - Compensation rules
- /controller/ - Controller configuration
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
