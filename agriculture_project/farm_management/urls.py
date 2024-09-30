# farm_management/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from .views import login_view, edit_farm
from farm_management.views import login_view



urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('farm_list/', views.farm_list_view, name='farm_list'),
    path('farm/<int:farm_id>/', views.farm_detail, name='farm_detail'),
    path('farm/add/', views.add_farm, name='add_farm'),
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'),
    path('edit_farm/<int:farm_id>/', views.edit_farm, name='edit_farm'),
]
