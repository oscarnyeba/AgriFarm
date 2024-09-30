from django.db.models import Q
from .models import Crop
from decimal import Decimal

from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def assess_crop_suitability(crop, temperature, rainfall, humidity):
    # Convert all inputs to Decimal for consistent calculations
    temperature = Decimal(str(temperature))
    rainfall = Decimal(str(rainfall))
    humidity = Decimal(str(humidity))

    # Calculate temperature suitability
    ideal_temp = (crop.ideal_temperature_min + crop.ideal_temperature_max) / 2
    temp_range = (crop.ideal_temperature_max - crop.ideal_temperature_min) / 2
    temp_suitability = 1 - min(abs(temperature - ideal_temp) / temp_range, Decimal('1'))

    # Calculate rainfall suitability
    ideal_rainfall = (crop.ideal_rainfall_min + crop.ideal_rainfall_max) / 2
    rainfall_range = (crop.ideal_rainfall_max - crop.ideal_rainfall_min) / 2
    rainfall_suitability = 1 - min(abs(rainfall - ideal_rainfall) / rainfall_range, Decimal('1'))

    # Calculate humidity suitability
    ideal_humidity = (crop.ideal_humidity_min + crop.ideal_humidity_max) / 2
    humidity_range = (crop.ideal_humidity_max - crop.ideal_humidity_min) / 2
    humidity_suitability = 1 - min(abs(humidity - ideal_humidity) / humidity_range, Decimal('1'))

    # Calculate overall suitability (simple average)
    overall_suitability = (temp_suitability + rainfall_suitability + humidity_suitability) / 3

    return overall_suitability


from decimal import Decimal

def calculate_confidence(crop, temperature, rainfall, humidity):
    # Convert all inputs to Decimal
    temperature = Decimal(str(temperature))
    rainfall = Decimal(str(rainfall))
    humidity = Decimal(str(humidity))

    # Convert crop attributes to Decimal
    ideal_temp_min = Decimal(str(crop.ideal_temperature_min))
    ideal_temp_max = Decimal(str(crop.ideal_temperature_max))
    ideal_rainfall_min = Decimal(str(crop.ideal_rainfall_min))
    ideal_rainfall_max = Decimal(str(crop.ideal_rainfall_max))
    ideal_humidity_min = Decimal(str(crop.ideal_humidity_min))
    ideal_humidity_max = Decimal(str(crop.ideal_humidity_max))

    # Calculate temperature confidence
    temp_confidence = Decimal('1') - abs(temperature - (ideal_temp_min + ideal_temp_max) / Decimal('2')) / ((ideal_temp_max - ideal_temp_min) / Decimal('2'))
    temp_confidence = max(Decimal('0'), min(temp_confidence, Decimal('1')))

    # Calculate rainfall confidence
    rainfall_confidence = Decimal('1') - abs(rainfall - (ideal_rainfall_min + ideal_rainfall_max) / Decimal('2')) / ((ideal_rainfall_max - ideal_rainfall_min) / Decimal('2'))
    rainfall_confidence = max(Decimal('0'), min(rainfall_confidence, Decimal('1')))

    # Calculate humidity confidence
    humidity_confidence = Decimal('1') - abs(humidity - (ideal_humidity_min + ideal_humidity_max) / Decimal('2')) / ((ideal_humidity_max - ideal_humidity_min) / Decimal('2'))
    humidity_confidence = max(Decimal('0'), min(humidity_confidence, Decimal('1')))

    # Calculate overall confidence
    overall_confidence = (temp_confidence + rainfall_confidence + humidity_confidence) / Decimal('3')

    # Convert to percentage and round to 2 decimal places
    confidence_percentage = float(round(overall_confidence * Decimal('100'), 2))

    return confidence_percentage

def get_crop_recommendations(farm, temperature, rainfall, humidity):
    logger.debug(f"get_crop_recommendations called with: farm={farm}, temp={temperature}, rainfall={rainfall}, humidity={humidity}")
    
    all_crops = Crop.objects.all()
    recommendations = []

    for crop in all_crops:
        suitability_score = assess_crop_suitability(crop, temperature, rainfall, humidity)
        recommendation = {
            'crop_name': crop.crop_name,
            'predicted_yield': calculate_predicted_yield(crop, temperature, rainfall, humidity),
            'confidence': calculate_confidence(crop, temperature, rainfall, humidity),
            'suitability': suitability_score
        }
        recommendations.append(recommendation)
    
    logger.debug(f"Recommendations: {recommendations}")
    return sorted(recommendations, key=lambda x: x['suitability'], reverse=True)[:5]

def calculate_predicted_yield(crop, temperature, rainfall, humidity):
    # Convert all inputs to Decimal
    temperature = Decimal(str(temperature))
    rainfall = Decimal(str(rainfall))
    humidity = Decimal(str(humidity))
    base_yield = Decimal(str(getattr(crop, 'average_yield', 100)))

    # Convert crop attributes to Decimal
    ideal_temp_min = Decimal(str(crop.ideal_temperature_min))
    ideal_temp_max = Decimal(str(crop.ideal_temperature_max))
    ideal_rainfall_min = Decimal(str(crop.ideal_rainfall_min))
    ideal_rainfall_max = Decimal(str(crop.ideal_rainfall_max))
    ideal_humidity_min = Decimal(str(crop.ideal_humidity_min))
    ideal_humidity_max = Decimal(str(crop.ideal_humidity_max))

    # Calculate temperature factor
    temp_factor = Decimal('1') - abs(temperature - (ideal_temp_min + ideal_temp_max) / Decimal('2')) / ((ideal_temp_max - ideal_temp_min) / Decimal('2'))
    temp_factor = max(Decimal('0.5'), min(temp_factor, Decimal('1')))

    # Calculate rainfall factor
    rainfall_factor = Decimal('1') - abs(rainfall - (ideal_rainfall_min + ideal_rainfall_max) / Decimal('2')) / ((ideal_rainfall_max - ideal_rainfall_min) / Decimal('2'))
    rainfall_factor = max(Decimal('0.5'), min(rainfall_factor, Decimal('1')))

    # Calculate humidity factor
    humidity_factor = Decimal('1') - abs(humidity - (ideal_humidity_min + ideal_humidity_max) / Decimal('2')) / ((ideal_humidity_max - ideal_humidity_min) / Decimal('2'))
    humidity_factor = max(Decimal('0.5'), min(humidity_factor, Decimal('1')))

    # Calculate predicted yield
    predicted_yield = base_yield * temp_factor * rainfall_factor * humidity_factor

    # Round to 2 decimal places and return as float
    return float(round(predicted_yield, 2))

