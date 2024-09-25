from django.db import transaction
from django.db.models import Q
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .decorators import farm_owner_required
from django.urls import reverse
from .models import Farm, Crop, WeatherData, Recommendation, Profile, User, Alert, CropRotation
from .forms import FarmForm, WeatherDataForm, RecommendationForm, RegistrationForm
from django.conf import settings
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect 
from decimal import Decimal
from soilgrids import SoilGrids
from django.http import JsonResponse
from .utils import send_email_alert, send_push_notification
from .ai_models import predict_crop_rotation, predict_crop_yield
from .weather_service import get_weather_forecast
from django.core.mail import send_mail
from django.template.loader import render_to_string

# Debug logging
logging.basicConfig(level=logging.DEBUG)

#registration view
def register(request):
    logging.debug("Entering register view")
    form = RegistrationForm() 
    if request.method == 'POST':
        logging.debug("Processing POST request for registration")
        form = RegistrationForm(request.POST)
        if form.is_valid():
            logging.debug("Registration form is valid")
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['username']
            user.save()
            logging.debug(f"User saved: {user.username}")
            
            # Create Profile
            Profile.objects.create(
                user=user,
                user_type=form.cleaned_data['user_type']
            )
            logging.debug(f"Profile created for user: {user.username}")

            # Log registration event
            logging.info(f"User registered: {user.username}")

            # Auto-login after registration
            login(request, user)
            logging.debug(f"User logged in: {user.username}")
          # Redirect based on user type
            profile = Profile.objects.get(user=user)
            if profile.user_type == 1:  # Farmer
                logging.debug(f"Redirecting farmer to farm_list")
                return redirect(reverse('farm_list'))
            elif profile.user_type == 2:  # Expert
                logging.debug(f"Redirecting expert to expert_profile")
                return redirect('expert_profile')
        else:
            logging.warning(f"Invalid registration form: {form.errors}")
    
    logging.debug("Rendering registration form")
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logging.debug(f"Logging out user: {request.user.username}")
    logout(request)
    return redirect('login')

#login view
@csrf_protect
def login_view(request):
    logging.debug("Entering login view")
    if request.method == 'POST':
        logging.debug("Processing POST request for login")
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            logging.debug("Login form is valid")
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                logging.debug(f"User authenticated: {user.username}")
                try:
                    profile = Profile.objects.get(user=user)
                    # Redirect based on user type
                    if profile.user_type == 1:  # Farmer
                        logging.debug(f"Redirecting farmer to farm_list")
                        return redirect('farm_list')
                    elif profile.user_type == 2:  # Expert
                        logging.debug(f"Redirecting expert to expert_profile")
                        return redirect('expert_profile')
                except Profile.DoesNotExist:
                    logging.error(f"Profile for user {user.username} does not exist.")
                    form.add_error(None, "Profile does not exist.")
            else:
                logging.warning("Invalid login attempt")
                form.add_error(None, "Invalid username or password.")
        else:
            logging.warning(f"Invalid login form: {form.errors}")
            form.add_error(None, "Invalid form submission.")
    elif request.user.is_authenticated:
        logging.debug(f"User already authenticated: {request.user.username}")
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.user_type == 1:  # Farmer
                logging.debug(f"Redirecting farmer to farm_list")
                return redirect('farm_list')
            elif profile.user_type == 2:  # Expert
                logging.debug(f"Redirecting expert to expert_profile")
                return redirect('expert_profile')
        except Profile.DoesNotExist:
            logging.error(f"Profile for user {request.user.username} does not exist.")
            return redirect('login')
    else:
        logging.debug("Rendering login form")
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})

# ** Farmer Profile Page **
@login_required
def farmer_profile(request):
    logging.debug("Entering farmer_profile view")
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 1:  # Only Farmers can access this page
        logging.warning(f"Non-farmer user {request.user.username} attempted to access farmer profile")
        return redirect('login')
    
    farms = Farm.objects.filter(user=request.user)
    logging.debug(f"Fetched {farms.count()} farms for user {request.user.username}")
    return render(request, 'farm_management/farm_list.html', {
        'profile': profile,
        'farms': farms,
    })
    
# ** Expert Profile Page **
@login_required
def expert_profile(request):
    logging.debug("Entering expert_profile view")
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 2:  # Only Experts can access this page
        logging.warning(f"Non-expert user {request.user.username} attempted to access expert profile")
        return redirect('login')

    return render(request, 'farm_management/expert_profile.html')

# ** Farm List for Farmers **
@login_required
def farm_list_view(request):
    logging.debug("Entering farm_list_view")
    query = request.GET.get('q', '') 
    farms = Farm.objects.filter(user=request.user)
    if query:
        logging.debug(f"Filtering farms with query: {query}")
        farms = farms.filter(farm_name__icontains=query)
    
    paginator = Paginator(farms, 10)  # Show 10 farms per page
    page = request.GET.get('page')
    try:
        farms = paginator.page(page)
    except PageNotAnInteger:
        farms = paginator.page(1)
    except EmptyPage:
        farms = paginator.page(paginator.num_pages)

    logging.debug(f"Rendering farm list with {farms.count()} farms")
    return render(request, 'farm_management/farm_list.html', {'farms': farms, 'query': query})

@login_required
def generate_crop_recommendation(farm, weather_info):
    logging.debug(f"Generating crop recommendation for farm: {farm.id}")
    try:
        # If weather data is unavailable, return an empty list
        if not weather_info or any(value == 'N/A' for value in weather_info.values()):
            logging.warning('Weather data is unavailable or contains N/A values.')
            return []

        # Convert weather data to Decimal for comparison
        current_temperature = Decimal(weather_info['main']['temp'])
        current_humidity = Decimal(weather_info['main']['humidity'])
        current_rainfall = Decimal(weather_info.get('rain', {}).get('1h', 0))

        # Get soil data
        soil_data = fetch_soil_data(farm.latitude, farm.longitude)
        logging.debug(f"Fetched soil data: {soil_data}")

        # Get historical crop data
        historical_crops = CropRotation.objects.filter(farm=farm).order_by('-year')[:3]
        logging.debug(f"Fetched {historical_crops.count()} historical crops")

        # Use AI model to predict best crop rotation
        recommended_crops = predict_crop_rotation(
            current_temperature, 
            current_humidity, 
            current_rainfall, 
            soil_data, 
            historical_crops
        )
        logging.debug(f"AI model recommended {len(recommended_crops)} crops")

        # For each recommended crop, predict yield
        for crop in recommended_crops:
            crop.predicted_yield = predict_crop_yield(
                crop, 
                current_temperature, 
                current_humidity, 
                current_rainfall, 
                soil_data
            )
            logging.debug(f"Predicted yield for {crop.name}: {crop.predicted_yield}")

        return recommended_crops
    except Exception as e:
        logging.error(f"Error in generating crop recommendation: {e}")
        return []

# ... (rest of the code remains unchanged)
