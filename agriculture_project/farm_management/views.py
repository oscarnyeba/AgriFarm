from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Farm, Crop, WeatherData, Recommendation
from .forms import FarmForm, WeatherDataForm, RecommendationForm
from django.conf import settings
import requests
import logging
from datetime import datetime, timedelta



def farm_list(request):
    query = request.GET.get('q', '') 
    if query:
        farms = Farm.objects.filter(farm_name__icontains=query)
    else:
        farms = Farm.objects.all()
    return render(request, 'farm_management/farm_list.html', {'farms': farms})

def generate_crop_recommendation(farm, weather_info):
    """
    Generate crop recommendations based on current weather data.
    """
    # If weather data is unavailable, return an empty list
    if not weather_info or any(value == 'N/A' for value in weather_info.values()):
        return []

    # Convert weather data to floats for comparison
    current_temperature = float(weather_info['temperature'])
    current_humidity = float(weather_info['humidity'])
    current_rainfall = float(weather_info['rainfall'])

    # Filter crops based on the ideal conditions
    recommended_crops = Crop.objects.filter(
        ideal_temperature_min__lte=current_temperature,
        ideal_temperature_max__gte=current_temperature,
        ideal_humidity_min__lte=current_humidity,
        ideal_humidity_max__gte=current_humidity,
        ideal_rainfall_min__lte=current_rainfall,
        ideal_rainfall_max__gte=current_rainfall,
    )

    return recommended_crops


def farm_detail(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    today = datetime.now().date()

        
     # Fetch weather data for today
    weather_data_today = WeatherData.objects.filter(farm=farm, date=today).first()
   
    # If no weather data is saved for today, attempt to fetch it from the API
    if not weather_data_today:
        weather_info = fetch_weather_data(farm.location, None)  # Fetch current weather from API
        if weather_info:
            # If fetched from the API, save the new weather data for today
            weather_data_today, created = WeatherData.objects.update_or_create(
                farm=farm,
                date=today,
                defaults={
                    'temperature': weather_info['temperature'],
                    'humidity': weather_info['humidity'],
                    'rainfall': weather_info['rainfall'],
                }
            )

    # Fetch weather history (only dates before today)
    weather_history = WeatherData.objects.filter(farm=farm, date__lt=today).order_by('-date')[:10]

    # Generate crop recommendations based on today's weather data
    recommendations = generate_crop_recommendation(farm, {
        'temperature': weather_data_today.temperature if weather_data_today else 'N/A',
        'humidity': weather_data_today.humidity if weather_data_today else 'N/A',
        'rainfall': weather_data_today.rainfall if weather_data_today else 'N/A',
    })

    context = {
        'farm': farm,
        'weather_info': weather_data_today,  # Pass today's weather info for current display
        'weather_data': weather_history,     # Pass weather history excluding today
        'recommendations': recommendations,  # Pass crop recommendations
    }
    return render(request, 'farm_management/farm_detail.html', context)

def add_farm(request):
    if request.method == 'POST':
        form = FarmForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('farm_list')
    else:
        form = FarmForm()
    return render(request, 'farm_management/farm_form.html', {'form': form})

def add_weather_data(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    weather_info = None

    if request.method == 'POST':
        form = WeatherDataForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['date']
             # Check if weather data for the selected date already exists
            weather_data_exists = WeatherData.objects.filter(farm=farm, date=selected_date).exists()
            if not weather_data_exists:
                # If not in DB, fetch weather from the API for the selected date
                weather_info = fetch_weather_data(farm.location, selected_date)

            if weather_info:
                weather_data = form.save(commit=False)
                weather_data.farm = farm
                weather_data.temperature = weather_info.get('temperature',0)
                weather_data.humidity = weather_info.get('humidity',0)
                weather_data.rainfall = weather_info.get('rainfall',0)
                weather_data.save()
                return redirect('farm_detail', farm_id=farm.id)
            else:
                form.add_error(None, 'Failed to fetch weather data from the API')  # Custom error message
        else:
            form.add_error(None, f"Weather data for {selected_date} already exists.")
    else:
        form = WeatherDataForm()


    return render(request, 'farm_management/weather_data_form.html', {
        'form': form,
        'farm': farm,
        'weather_info': weather_info  # Pass the fetched weather info to the template
    })

def fetch_weather_data(location, date= None):
    """
    Function to fetch weather data from OpenWeather based on farm location (city name or coordinates)
    """
    api_key = settings.WEATHER_API_KEY
    api_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"

    logging.info(f"Fetching weather data for {location} on {date}")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        weather_data = response.json()
        logging.info(f'Weather data fetched {weather_data}')
        temperature = weather_data.get('main', {}).get('temp', 'N/A')  
        humidity = weather_data.get('main', {}).get('humidity', 'N/A')  
        rainfall = weather_data.get('rain', {}).get('1h', 0) 

        return {
            'temperature': temperature,
            'humidity': humidity,
            'rainfall': rainfall
            }
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred during API call: {e}")
        return None
