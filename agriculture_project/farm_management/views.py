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
from .forms import FarmForm, WeatherDataForm, RecommendationForm, CustomUserCreationForm
from django.conf import settings
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect 
from decimal import Decimal
from django.http import JsonResponse
from .utils import send_email_alert, send_push_notification, create_alert
from .prediction import generate_crop_recommendation
from .weather_service import get_weather_forecast
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib import messages

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
        farms = farms.filter(farm_name__icontains=query)
    paginator = Paginator(farms, 10)
    page = request.GET.get('page')
    try:
        farms = paginator.page(page)
    except PageNotAnInteger:
        farms = paginator.page(1)
    except EmptyPage:
        farms = paginator.page(paginator.num_pages)
    return render(request, 'farm_management/farm_list.html', {'farms': farms, 'query': query})

@farm_owner_required
@login_required
def farm_detail(request, farm_id):
    farm = get_object_or_404(Farm.objects.prefetch_related('weatherdata_set'), id=farm_id, user=request.user)
    today = datetime.now().date()
    five_days_ago = today - timedelta(days=5)

    # Fetch or update weather data
    weather_data_today = fetch_or_update_weather_data(farm, today)
    weather_history = farm.weatherdata_set.filter(date__gte=five_days_ago, date__lte=today).order_by('-date')

    # Fetch current weather info
    weather_info = fetch_weather_data(farm.location, None)
    if weather_info is None:
        logging.error(f"Failed to fetch weather data for farm: {farm.farm_name}, location: {farm.location}")
        weather_info = {}
        messages.warning(request, 'Unable to fetch current weather data at the moment')
    else:
        # Convert Unix timestamps to datetime objects
        weather_info['sys']['sunrise'] = datetime.fromtimestamp(weather_info['sys']['sunrise'])
        weather_info['sys']['sunset'] = datetime.fromtimestamp(weather_info['sys']['sunset'])
        weather_info['dt'] = datetime.fromtimestamp(weather_info['dt'])

    # Generate crop recommendations
    try:
        historical_crops = CropRotation.objects.filter(farm=farm).order_by('-year')[:3]
        recommendations = generate_crop_recommendation(farm, weather_info, historical_crops)
        print(f"Debug: Recommendations generated: {recommendations}")
    except Exception as e:
        logging.error(f"Error generating crop recommendations: {e}")
        recommendations = []
        messages.warning(request, 'Unable to generate crop recommendations at the moment')

    # Fetch weather forecast and check for extreme weather
    try:
        weather_forecast = get_weather_forecast(farm.latitude, farm.longitude)
        if weather_forecast:
            check_extreme_weather(farm, weather_forecast)
        else:
            messages.warning(request, 'Unable to fetch weather forecast at the moment')
    except Exception as e:
        logging.error(f"Error fetching weather forecast: {e}")
        weather_forecast = None
        messages.warning(request, 'Unable to fetch weather forecast at the moment')

    # Assess weather impact on crops
    try:
        current_crops = CropRotation.objects.filter(farm=farm, year=datetime.now().year)
        weather_impacts = []
        if weather_forecast:
            for day in weather_forecast:
                for crop_rotation in current_crops:
                    impact = assess_weather_impact(crop_rotation.crop, day)
                    if impact:
                        weather_impacts.append({
                            'date': day['date'],
                            'crop': crop_rotation.crop.name,
                            'impact': impact
                        })
    except Exception as e:
        logging.error(f"Error assessing weather impact: {e}")
        weather_impacts = []
        messages.warning(request, 'Unable to assess weather impact on crops at the moment')

    context = {
        'farm': farm,
        'weather_info': weather_info,
        'weather_data': weather_history,
        'weather_data_today': weather_data_today,
        'recommendations': recommendations,
        'weather_forecast': weather_forecast,
        'weather_impacts': weather_impacts,
    }
    return render(request, 'farm_management/farm_detail.html', context)

def fetch_or_update_weather_data(farm, date):
    weather_data = WeatherData.objects.filter(farm=farm, date=date).first()
    if not weather_data:
        try:
            weather_info = fetch_weather_data(farm.location, None)
            if weather_info:
                with transaction.atomic():
                    weather_data, created = WeatherData.objects.update_or_create(
                        farm=farm,
                        date=date,
                        defaults={
                            'temperature': weather_info['main']['temp'],
                            'feels_like': weather_info['main']['feels_like'],
                            'temp_min': weather_info['main']['temp_min'],
                            'temp_max': weather_info['main']['temp_max'],
                            'pressure': weather_info['main']['pressure'],
                            'humidity': weather_info['main']['humidity'],
                            'visibility': weather_info['visibility'],
                            'wind_speed': weather_info['wind']['speed'],
                            'wind_direction': weather_info['wind']['deg'],
                            'wind_gust': weather_info['wind'].get('gust', 0),
                            'cloudiness': weather_info['clouds']['all'],
                            'rainfall': weather_info.get('rain', {}).get('1h', 0),
                            'weather_main': weather_info['weather'][0]['main'],
                            'weather_description': weather_info['weather'][0]['description'],
                            'weather_icon': weather_info['weather'][0]['icon'],
                        }
                    )
                logging.info(f"Weather data {'created' if created else 'updated'} for {date}")
            else:
                logging.warning("No weather info fetched from API")
        except Exception as e:
            logging.error(f"Error fetching weather data: {e}")
    else:
        logging.info(f"Using existing weather data for {date}")
    return weather_data

@login_required
@csrf_protect
def add_farm(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 1:
        return redirect('login')
    if request.method == 'POST':
        form = FarmForm(request.POST)
        try:
            if form.is_valid():
                location = form.cleaned_data['location']
                if latitude is None or longitude is None:
                    logging.error(f"Geocoding failed for location: {location}")
                    form.add_error('location', 'Unable to fetch latitude and longitude for this location.')
                    return render(request, 'farm_management/farm_form.html', {'form': form})
                with transaction.atomic():
                    farm = form.save(commit=False)
                    farm.user = request.user
                    farm.latitude = latitude
                    farm.longitude = longitude
                    farm.save()
                logging.info(f"Farm added successfully: {farm.farm_name} at {latitude}, {longitude}")
                return redirect(reverse('farm_list'))
        except Exception as e:
            logging.error(f"An error occurred while saving the form: {e}")
            form.add_error(None, 'An error occurred while saving the farm. Please try again.')
    else:
        form = FarmForm()
    return render(request, 'farm_management/farm_form.html', {'form': form})

def fetch_weather_data(location, date=None):
    if not location or not isinstance(location, str):
        logging.error("Invalid location provided.")
        return None
    logging.info(f"Fetching weather data for {location} on {date}")
    try:
        api_key = settings.WEATHER_API_KEY
        api_url = f"https://pro.openweathermap.org/data/3.0/forecast/climate?q={location}&appid={api_key}&units=metric"
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
        logging.info(f'Weather data fetched: {weather_data}')
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


@login_required
@csrf_protect
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        return redirect('farm_list')
    return render(request, 'farm_management/edit_profile.html', {'user': user})

def check_extreme_weather(farm, weather_forecast):
    if not weather_forecast:
        logging.warning(f"No weather forecast available for farm {farm.id}")
        return
    for day in weather_forecast:
        if day['rainfall'] > 50:
            create_alert(farm, f"Heavy rainfall expected on {day['date']}: {day['rainfall']}mm")
        if day['temp_min'] < 0:
            create_alert(farm, f"Frost warning for {day['date']}: Minimum temperature {day['temp_min']}°C")
        if day['temp_max'] > 35:
            create_alert(farm, f"Extreme heat warning for {day['date']}: Maximum temperature {day['temp_max']}°C")
        if day['rainfall'] < 5 and day['temp_max'] > 30:
            create_alert(farm, f"Drought alert for {day['date']}: High temperature and low rainfall")
        if day.get('wind_speed', 0) > 60:
            create_alert(farm, f"Strong wind alert for {day['date']}: Wind speed {day['wind_speed']} km/h")
        if day['temp_max'] > 30 and day['rainfall'] > 0 and day.get('humidity', 0) > 70:
            create_alert(farm, f"Potential hail risk on {day['date']}: High temperature, rainfall, and humidity")
        if 'temp_max' in day and 'temp_min' in day and (day['temp_max'] - day['temp_min']) > 15:
            create_alert(farm, f"Sudden temperature drop alert for {day['date']}: High {day['temp_max']}°C, Low {day['temp_min']}°C")

def create_alert(farm, message):
    alert = Alert.objects.create(farm=farm, message=message)
    subject = f"Weather Alert for {farm.farm_name}"
    html_message = render_to_string('farm_management/weather_alert.html', {'farm': farm, 'message': message})
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [farm.user.email], html_message=html_message)
    send_push_notification(farm.user, message)
    return alert

@login_required
def view_alerts(request):
    alerts = Alert.objects.filter(farm__user=request.user).order_by('-created_at')
    return render(request, 'farm_management/alerts.html', {'alerts': alerts})

@login_required
def crop_rotation_suggestion(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)
    weather_info = fetch_weather_data(farm.location)
    historical_crops = CropRotation.objects.filter(farm=farm).order_by('-year')[:3]
    suggested_crops = predict_crop_rotation(
        weather_info['main']['temp'],
        weather_info['main']['humidity'],
        weather_info.get('rain', {}).get('1h', 0),
        historical_crops
    )
    context = {
        'farm': farm,
        'suggested_crops': suggested_crops,
        'weather_info': weather_info,
    }
    return render(request, 'farm_management/crop_rotation_suggestion.html', context)

@login_required
def crop_yield_prediction(request, farm_id, crop_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)
    crop = get_object_or_404(Crop, id=crop_id)
    weather_info = fetch_weather_data(farm.location)
    predicted_yield = predict_crop_yield(
        crop,
        weather_info['main']['temp'],
        weather_info['main']['humidity'],
        weather_info.get('rain', {}).get('1h', 0),
    )
    context = {
        'farm': farm,
        'crop': crop,
        'predicted_yield': predicted_yield,
        'weather_info': weather_info,
    }
    return render(request, 'farm_management/crop_yield_prediction.html', context)

@login_required
def weather_impact(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id, user=request.user)
    weather_forecast = get_weather_forecast(farm.latitude, farm.longitude)
    current_crops = CropRotation.objects.filter(farm=farm, year=datetime.now().year)
    impacts = []
    for day in weather_forecast:
        for crop in current_crops:
            impact = assess_weather_impact(crop.crop, day)
            if impact:
                impacts.append({
                    'date': day['date'],
                    'crop': crop.crop,
                    'impact': impact
                })
    context = {
        'farm': farm,
        'weather_forecast': weather_forecast,
        'impacts': impacts,
    }
    return render(request, 'farm_management/weather_impact.html', context)

def assess_weather_impact(crop, weather):
    impact = []
    if weather['temp_max'] > crop.ideal_temperature_max:
        impact.append(f"High temperature may stress {crop.name}")
    elif weather['temp_min'] < crop.ideal_temperature_min:
        impact.append(f"Low temperature may damage {crop.name}")
    if weather['rainfall'] > crop.ideal_rainfall_max:
        impact.append(f"Excessive rainfall may waterlog {crop.name}")
    elif weather['rainfall'] < crop.ideal_rainfall_min:
        impact.append(f"Insufficient rainfall may require irrigation for {crop.name}")
    if weather['humidity'] > crop.ideal_humidity_max:
        impact.append(f"High humidity may increase disease risk for {crop.name}")
    elif weather['humidity'] < crop.ideal_humidity_min:
        impact.append(f"Low humidity may cause water stress for {crop.name}")
    return impact if impact else None

@login_required
def weather_alert(request):
    user = request.user
    farms = Farm.objects.filter(user=user)
    alerts = []
    for farm in farms:
        weather_forecast = get_weather_forecast(farm.latitude, farm.longitude)
        if weather_forecast:
            current_crops = CropRotation.objects.filter(farm=farm, year=datetime.now().year)
            for day in weather_forecast:
                for crop_rotation in current_crops:
                    impacts = assess_weather_impact(crop_rotation.crop, day)
                    if impacts:
                        alert_message = f"Weather alert for {farm.farm_name} on {day['date']}:\n"
                        alert_message += "\n".join(impacts)
                        alert = create_alert(farm, alert_message)
                        alerts.append(alert)
    context = {
        'alerts': alerts,
    }
    return render(request, 'farm_management/weather_alerts.html', context)
