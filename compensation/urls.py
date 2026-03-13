# compensation/urls.py
"""
URL routing for compensation configuration.
"""

from django.urls import path
from . import views

app_name = 'compensation'

urlpatterns = [
    # Rules list
    path('', views.rule_list, name='rule_list'),
    
    # Rule CRUD
    path('rule/add/', views.rule_add, name='rule_add'),
    path('rule/<int:rule_id>/', views.rule_edit, name='rule_edit'),
    path('rule/<int:rule_id>/delete/', views.rule_delete, name='rule_delete'),
    
    # Rule actions
    path('rule/<int:rule_id>/reset/', views.rule_reset, name='rule_reset'),
    path('rule/<int:rule_id>/toggle/', views.rule_toggle, name='rule_toggle'),
    
    # Event log
    path('events/', views.event_list, name='event_list'),
    path('rule/<int:rule_id>/events/', views.rule_events, name='rule_events'),
]
