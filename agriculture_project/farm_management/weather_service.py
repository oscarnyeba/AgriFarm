import requests
from django.conf import settings
from datetime import datetime, timedelta
import logging

def get_weather_forecast(latitude, longitude, days=7):
    """
    Fetch weather forecast for the given coordinates.
    
    :param latitude: Latitude of the location
    :param longitude: Longitude of the location
    :param days: Number of days to forecast (default is 7)
    :return: List of dictionaries containing weather data for each day
    """
    api_key = settings.WEATHER_API_KEY
    api_url = f"https://pro.openweathermap.org/data/3.0/forecast/climate?q={location}&appid={api_key}&units=metric"

    
    params = {
        'lat': latitude,
        'lon': longitude,
        'exclude': 'current,minutely,hourly,alerts',
        'units': 'metric',
        'appid': api_key
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        forecast = []
        for day_data in data['daily'][:days]:
            forecast.append({
                'date': datetime.fromtimestamp(day_data['dt']).date(),
                'temp_max': day_data['temp']['max'],
                'temp_min': day_data['temp']['min'],
                'humidity': day_data['humidity'],
                'wind_speed': day_data['wind_speed'],
                'rainfall': day_data.get('rain', 0),  # Rain in mm, 0 if not present
                'weather_description': day_data['weather'][0]['description']
            })
        
        return forecast_data
    
    except Exception as e:
        logging.error(f"Error fetching weather forecast: {e}")
        return None
