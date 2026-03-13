# controller/urls.py
"""
URL routing for controller configuration.
"""

from django.urls import path
from . import views

app_name = 'controller'

urlpatterns = [
    # Controller list
    path('', views.controller_list, name='controller_list'),
    
    # Controller CRUD
    path('add/', views.controller_add, name='controller_add'),
    path('<int:controller_id>/', views.controller_edit, name='controller_edit'),
    path('<int:controller_id>/delete/', views.controller_delete, name='controller_delete'),
    
    # Actions
    path('<int:controller_id>/test/', views.controller_test, name='controller_test'),
]
