"""
URL configuration for agent services
"""
from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('concierge/', views.concierge_chat, name='concierge'),
]
