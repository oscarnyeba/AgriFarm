from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Farm, Crop, WeatherData, Recommendation
from .forms import FarmForm, WeatherDataForm, RecommendationForm
from django.conf import settings
import requests

def farm_list(request):
    query = request.GET.get('q', '')  # Default to empty string if query is None
    if query:
        farms = Farm.objects.filter(farm_name__icontains=query)
    else:
        farms = Farm.objects.all()
    return render(request, 'farm_management/farm_list.html', {'farms': farms})

def farm_detail(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    weather_data = WeatherData.objects.filter(farm=farm).order_by('-date')[:10]
    recommendations = Recommendation.objects.filter(farm=farm).order_by('-date')[:5]
    context = {
        'farm': farm,
        'weather_data': weather_data,
        'recommendations': recommendations,
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
            weather_data = form.save(commit=False)
            weather_data.farm = farm
            weather_data.save()
            return redirect('farm_detail', farm_id=farm.id)
    else:
        form = WeatherDataForm()
    return render(request, 'farm_management/weather_data_form.html', {'form': form, 'farm': farm})

def add_recommendation(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    if request.method == 'POST':
        form = RecommendationForm(request.POST)
        if form.is_valid():
            recommendation = form.save(commit=False)
            recommendation.farm = farm
            recommendation.save()
            return redirect('farm_detail', farm_id=farm.id)
    else:
        form = RecommendationForm()
    return render(request, 'farm_management/recommendation_form.html', {'form': form, 'farm': farm})

def farm_list(request):
    query = request.GET.get('q')
    if query:
        farms = Farm.objects.filter(farm_name__icontains=query)  # Filter farms by name
    else:
        farms = Farm.objects.all()  # Show all farms if no search query

    return render(request, 'farm_management/farm_list.html', {'farms': farms})

# API Key for weather (replace with your actual API key)
WEATHER_API_KEY = 'your_api_key'  # Add this to your Django settings securely

def fetch_weather_data(location, date):
    """
    Function to fetch weather data from external API based on farm location and date
    """
    api_key = settings.WEATHER_API_KEY
    api_url = f"https://api.tomorrow.io/v4/weather/forecast?location={location}&apikey={api_key}&dt={date}"

    response = requests.get(api_url)

    if response.status_code == 200:
        weather_data = response.json()
        # Extract temperature, humidity, and rainfall from the API response (adjust based on API structure)
        forecast = weather_data['forecast']['forecastday'][0]['day']
        return {
            'temperature': forecast['avgtemp_c'],
            'humidity': forecast['avghumidity'],
            'rainfall': forecast['totalprecip_mm'],
        }
    else:
        return None  # Handle error or return default values

def add_weather_data(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    weather_info = None

    if request.method == 'POST':
        form = WeatherDataForm(request.POST)
        if form.is_valid():
            # Fetch weather data from the external API
            date = form.cleaned_data['date']
            weather_info = fetch_weather_data(farm.location, date)

            if weather_info:
                # If API returned valid data, store it in the database
                weather_data = form.save(commit=False)
                weather_data.farm = farm
                weather_data.temperature = weather_info['temperature']
                weather_data.humidity = weather_info['humidity']
                weather_data.rainfall = weather_info['rainfall']
                weather_data.save()
                return redirect('farm_detail', farm_id=farm.id)
            else:
                form.add_error(None, 'Failed to fetch weather data from the API')
    else:
        form = WeatherDataForm()

    return render(request, 'farm_management/weather_data_form.html', {
        'form': form,
        'farm': farm,
        'weather_info': weather_info  # Pass the fetched weather info to the template
    })
