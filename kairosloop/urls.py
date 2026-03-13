# kairosloop/urls.py
"""
Main URL routing for KairosLoop.

Structure:
    /dashboard/      - Live operator dashboard
    /measurement/    - Measurement configuration (gauges, channels, features)
    /compensation/   - Compensation rules
    /controller/     - Controller configuration
    /admin/          - Django admin
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main pages
    path('', include('dashboard.urls')),  # Dashboard at root
    path('measurement/', include('measurement.urls')),
    path('compensation/', include('compensation.urls')),
    path('controller/', include('controller.urls')),
]
