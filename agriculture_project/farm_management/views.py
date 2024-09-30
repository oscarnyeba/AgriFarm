from django.db import transaction
from django.db.models import Q
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .decorators import farm_owner_required
from django.urls import reverse
from .models import Farm, Crop, WeatherData, Recommendation, Profile, User
from .forms import FarmForm, CustomUserCreationForm
from django.conf import settings
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, date, time
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect 
from decimal import Decimal
from django.http import JsonResponse
from .weather_service import get_weather_forecast
from django.contrib import messages
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import json
from django.core.serializers.json import DjangoJSONEncoder
from .utils import assess_crop_suitability, get_crop_recommendations # Add this import at the top of the file
from itertools import groupby
from operator import itemgetter

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        return super().default(obj)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('farm_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                try:
                    profile = Profile.objects.get(user=user)
                    return redirect('farm_list')
                except Profile.DoesNotExist:
                    logging.error(f"Profile for user {user.username} does not exist.")
                    form.add_error(None, "Profile does not exist.")
            else:
                form.add_error(None, "Invalid username or password.")
        else:
            form.add_error(None, "Invalid form submission.")
    elif request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            return redirect('farm_list')
        except Profile.DoesNotExist:
            logging.error(f"Profile for user {request.user.username} does not exist.")
            return redirect('login')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def farmer_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 1:
        return redirect('login')
    farms = Farm.objects.filter(user=request.user)
    return render(request, 'farm_management/farm_list.html', {'profile': profile, 'farms': farms})

@login_required
def farm_list_view(request):
    query = request.GET.get('q', '') 
    farms = Farm.objects.filter(user=request.user)
    if query:
        farms = farms.filter(name__icontains=query)
    
    # Add ordering to the QuerySet
    farms = farms.order_by('name')  # Changed from 'farm_name' to 'name'
    
    paginator = Paginator(farms, 10)
    page = request.GET.get('page')
    try:
        farms = paginator.page(page)
    except PageNotAnInteger:
        farms = paginator.page(1)
    except EmptyPage:
        farms = paginator.page(paginator.num_pages)
    return render(request, 'farm_management/farm_list.html', {'farms': farms, 'query': query})
logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        return super().default(obj)


class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, time)):
            return obj.isoformat()
        return super().default(obj)

import logging

logger = logging.getLogger(__name__)

@farm_owner_required
@login_required
def farm_detail(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    
    # Get weather forecast
    forecast_data = get_weather_forecast(farm.latitude, farm.longitude)

    selected_day = request.GET.get('day', 0)
    try:
        selected_day = int(selected_day)
        if selected_day < 0 or selected_day >= len(forecast_data):
            selected_day = 0
    except ValueError:
        selected_day = 0

    # Get the selected day's forecast
    selected_forecast = forecast_data[selected_day]

    # Extract required weather parameters for crop recommendations
    temperature = selected_forecast.get('temp', 0)  # Use 0 as default if 'temp' is not found
    rainfall = selected_forecast.get('rainfall', 0)  # Use 0 as default if 'rainfall' is not found
    humidity = selected_forecast.get('humidity', 0)  # Use 0 as default if 'humidity' is not found

    # Print debug information
    print(f"Debug - Temperature: {temperature}, Rainfall: {rainfall}, Humidity: {humidity}")

    # Get crop recommendations with all required parameters
    crop_recommendations = get_crop_recommendations(
        farm=farm,
        temperature=temperature,
        rainfall=rainfall,
        humidity=humidity
    )

    context = {
        'farm': farm,
        'forecast_data': forecast_data,
        'crop_recommendations': crop_recommendations,
        'selected_day': selected_day,
        'selected_forecast': selected_forecast,
    }
    return render(request, 'farm_management/farm_detail.html', context)

@login_required
@csrf_protect
def add_farm(request, farm_id=None):
    if request.method == 'POST':
        form = FarmForm(request.POST)
        if form.is_valid():
            farm = form.save(commit=False)
            location = form.cleaned_data['location']
            
            # Use geopy to get the latitude and longitude
            geolocator = Nominatim(user_agent="your_app_name")
            geocode_result = geolocator.geocode(location)
            
            if geocode_result:
                farm.latitude = geocode_result.latitude
                farm.longitude = geocode_result.longitude
            else:
                # Handle the case where geocoding fails
                form.add_error('location', 'Could not geocode the provided location.')
                return render(request, 'farm_management/farm_form.html', {'form': form})
            
            farm.user = request.user
            farm.save()
            
            # Fetch weather data based on the stored latitude and longitude
            weather_forecast = get_weather_forecast(farm.latitude, farm.longitude)
            
            # Process weather data as needed
            
            logging.info(f"Farm added successfully: {farm.name} at {farm.latitude}, {farm.longitude}")
            return redirect(reverse('farm_list'))
    else:
        form = FarmForm()
    return render(request, 'farm_management/farm_form.html', {'form': form})

def fetch_weather_data(lat, lon, date=None):
    if not lat or not lon:
        logging.error("Invalid latitude or longitude provided.")
        return None
    logging.info(f"Fetching weather data for location at ({lat}, {lon}) on {date}")
    try:
        api_key = settings.WEATHER_API_KEY
        api_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        response = session.get(api_url, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        logging.info(f'Weather data fetched successfully')
        return weather_data
    except requests.exceptions.RequestException as e:
        logging.exception(f"Error occurred during API call: {e}")
        return None

@login_required
@csrf_protect
def edit_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    if request.user != farm.user:
        return redirect('farm_list')
    if request.method == 'POST':
        form = FarmForm(request.POST, instance=farm)
        if form.is_valid():
            form.save()
            return redirect('farm_detail', farm_id=farm.id)
    else:
        form = FarmForm(instance=farm)
    return render(request, 'farm_management/edit_farm.html', {'form': form, 'farm': farm})