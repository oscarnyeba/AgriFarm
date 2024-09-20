# farm_management/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from .views import login_view, ask_expert_view, edit_farm
from farm_management.views import login_view



urlpatterns = [
    path('', lambda request: redirect('login')),
    path('ask-expert/', ask_expert_view, name='ask_expert'),
    path('farm/edit/<int:farm_id>/', edit_farm, name='edit_farm'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('farm/<int:farm_id>/', views.farm_detail, name='farm_detail'),
    path('farm_list/', views.farm_list_view, name='farm_list'),
    path('farm/add/', views.add_farm, name='add_farm'),
    path('farm/<int:farm_id>/add_weather/', views.add_weather_data, name='add_weather_data'),
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'),
    path('expert/profile/', views.expert_profile, name='expert_profile'),


]
