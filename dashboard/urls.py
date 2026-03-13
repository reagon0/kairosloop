# dashboard/urls.py
"""
URL routing for dashboard app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # System Setup
    path('setup/', views.setup, name='setup'),
    path('setup/machine/', views.setup_machine, name='setup_machine'),
    
    # Gauge Configuration
    path('setup/gauge/add/', views.setup_gauge_add, name='setup_gauge_add'),
    path('setup/gauge/<int:gauge_id>/', views.setup_gauge_edit, name='setup_gauge_edit'),
    path('setup/gauge/<int:gauge_id>/delete/', views.setup_gauge_delete, name='setup_gauge_delete'),
    
    # Channel Configuration
    path('setup/gauge/<int:gauge_id>/channel/add/', views.setup_channel_add, name='setup_channel_add'),
    path('setup/channel/<int:channel_id>/', views.setup_channel_edit, name='setup_channel_edit'),
    path('setup/channel/<int:channel_id>/delete/', views.setup_channel_delete, name='setup_channel_delete'),
    
    # Controller Configuration
    path('setup/controller/add/', views.setup_controller_add, name='setup_controller_add'),
    path('setup/controller/<int:controller_id>/', views.setup_controller_edit, name='setup_controller_edit'),
    path('setup/controller/<int:controller_id>/delete/', views.setup_controller_delete, name='setup_controller_delete'),
    
    # Measurements (Features)
    path('measurements/', views.measurements, name='measurements'),
    path('measurements/add/', views.measurement_add, name='measurement_add'),
    path('measurements/<int:feature_id>/', views.measurement_edit, name='measurement_edit'),
    path('measurements/<int:feature_id>/delete/', views.measurement_delete, name='measurement_delete'),
]