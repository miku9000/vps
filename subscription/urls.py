from django.urls import path
from . import views

urlpatterns = [
    path('ostuleht/', views.subscription_home, name = 'ostuleht'),
    path('tulemus/', views.activate_user, name = 'tulemus')
]