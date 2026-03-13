# measurement/urls.py
"""
URL routing for measurement configuration.

Handles: Gauges, Channels, Features (measurements)
"""

from django.urls import path
from . import views

app_name = 'measurement'

urlpatterns = [
    # Main list
    path('', views.feature_list, name='feature_list'),
    
    # Features (measurements)
    path('feature/add/', views.feature_add, name='feature_add'),
    path('feature/<int:feature_id>/', views.feature_edit, name='feature_edit'),
    path('feature/<int:feature_id>/delete/', views.feature_delete, name='feature_delete'),
    
    # Gauges
    path('gauge/', views.gauge_list, name='gauge_list'),
    path('gauge/add/', views.gauge_add, name='gauge_add'),
    path('gauge/<int:gauge_id>/', views.gauge_edit, name='gauge_edit'),
    path('gauge/<int:gauge_id>/delete/', views.gauge_delete, name='gauge_delete'),
    
    # Channels
    path('gauge/<int:gauge_id>/channel/add/', views.channel_add, name='channel_add'),
    path('channel/<int:channel_id>/', views.channel_edit, name='channel_edit'),
    path('channel/<int:channel_id>/delete/', views.channel_delete, name='channel_delete'),
]
