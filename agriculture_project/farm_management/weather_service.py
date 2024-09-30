import requests
from django.conf import settings
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

def get_weather_forecast(latitude, longitude):
    print(f"Fetching weather forecast for lat: {latitude}, lon: {longitude}")
    logger.info(f"Fetching weather forecast for lat: {latitude}, lon: {longitude}")
    api_key = settings.WEATHER_API_KEY
    base_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        print(f"Weather API response: {response.text}")
        logger.info(f"Weather API response: {response.text}")
        data = response.json()
        forecast = []
        for item in data['list']:
            forecast_time = datetime.fromtimestamp(item['dt'])
            forecast_data = {
                'date': forecast_time.date(),
                'time': forecast_time.time(),
                'weather_main': item['weather'][0]['main'],
                'weather_description': item['weather'][0]['description'],
                'temp': item['main']['temp'],
                'temp_min': item['main'].get('temp_min', None),
                'temp_max': item['main'].get('temp_max', None),
                'feels_like': item['main'].get('feels_like', None),
                'pressure': item['main']['pressure'],
                'humidity': item['main']['humidity'],
                'visibility': item['visibility'],
                'wind_speed': item['wind']['speed'],
                'wind_deg': item['wind']['deg'],
                'clouds': item['clouds']['all'],
                'pop': item.get('pop', 0) * 100,  # Probability of precipitation
            }
            # Check if rain data is available
            if 'rain' in item and '3h' in item['rain']:
                forecast_data['rainfall'] = item['rain']['3h']
            else:
                forecast_data['rainfall'] = 0
            
            forecast.append(forecast_data)
        
        logging.debug(f"Forecast generated successfully: {forecast}")
        return forecast
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")  # Add this line
        return None
