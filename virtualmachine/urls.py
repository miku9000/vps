from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.vm_dashboard, name = 'dashboard'),
    path('start/', views.start_vm, name = 'start_vm'),
    path('stop/', views.stop_vm, name = 'stop_vm'),
    path('console/<int:vmid>/', views.vm_console, name = 'console')
]