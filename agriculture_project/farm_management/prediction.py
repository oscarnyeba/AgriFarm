from django.db import models
from .models import Farm, Crop

class CropRotationPrediction(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='crop_rotation_predictions')
    year = models.IntegerField()
    predicted_crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Predicted {self.predicted_crop.crop_name} for {self.farm.farm_name} in {self.year}"

    class Meta:
        unique_together = ('farm', 'year')
        ordering = ['-year', '-created_at']

class CropYieldPrediction(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='crop_yield_predictions')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    year = models.IntegerField()
    predicted_yield = models.FloatField()
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Predicted yield for {self.crop.crop_name} at {self.farm.farm_name} in {self.year}: {self.predicted_yield}"

    class Meta:
        unique_together = ('farm', 'crop', 'year')
        ordering = ['-year', '-created_at']

    
def predict_crop_rotation(temperature, humidity, rainfall, soil_data, historical_crops):
    """
    Predict the next crop in the rotation based on environmental factors and historical data.
    
    :param temperature: Average temperature (float)
    :param humidity: Average humidity (float)
    :param rainfall: Average rainfall (float)
    :param soil_data: Dictionary containing soil properties
    :param historical_crops: QuerySet of CropRotation objects for the last few years
    :return: List of suggested crops (Crop objects)
    """
    # This is a simplified prediction model. In a real-world scenario,
    # you would use more sophisticated machine learning models.
    
    suggested_crops = []
    
    # Get all available crops
    all_crops = Crop.objects.all()
    
    for crop in all_crops:
        score = 0
        
        # Check temperature suitability
        if crop.ideal_temperature_min <= temperature <= crop.ideal_temperature_max:
            score += 1
        
        # Check humidity suitability
        if crop.ideal_humidity_min <= humidity <= crop.ideal_humidity_max:
            score += 1
        
        # Check rainfall suitability
        if crop.ideal_rainfall_min <= rainfall <= crop.ideal_rainfall_max:
            score += 1
        
        # Check soil suitability (simplified)
        if soil_data.get('ph', 0) >= crop.min_ph and soil_data.get('ph', 0) <= crop.max_ph:
            score += 1
        
        # Avoid suggesting crops that were recently planted
        if not any(hc.crop == crop for hc in historical_crops):
            score += 1
        
        if score >= 3:  # Threshold for suggestion
            suggested_crops.append(crop)
    
    return suggested_crops

def predict_crop_yield(farm, crop, year, weather_data):
    """
    Predict the yield for a specific crop on a farm for a given year.
    
    :param farm: Farm object
    :param crop: Crop object
    :param year: Year for prediction (int)
    :param weather_data: Dictionary containing weather information
    :return: Predicted yield (float) and confidence (float)
    """
    # This is a simplified prediction model. In a real-world scenario,
    # you would use more sophisticated machine learning models.
    
    base_yield = crop.average_yield
    
    # Adjust yield based on weather conditions
    temperature_factor = 1.0
    if weather_data['temperature'] < crop.ideal_temperature_min:
        temperature_factor = 0.8
    elif weather_data['temperature'] > crop.ideal_temperature_max:
        temperature_factor = 0.9
    
    rainfall_factor = 1.0
    if weather_data['rainfall'] < crop.ideal_rainfall_min:
        rainfall_factor = 0.7
    elif weather_data['rainfall'] > crop.ideal_rainfall_max:
        rainfall_factor = 0.8
    
    # Consider historical yields
    historical_yields = CropYieldPrediction.objects.filter(
        farm=farm, 
        crop=crop, 
        year__lt=year
    ).order_by('-year')[:3]
    
    if historical_yields:
        avg_historical_yield = sum(hy.predicted_yield for hy in historical_yields) / len(historical_yields)
        historical_factor = avg_historical_yield / base_yield
    else:
        historical_factor = 1.0
    
    # Calculate predicted yield
    predicted_yield = base_yield * temperature_factor * rainfall_factor * historical_factor
    
    # Calculate confidence (simplified)
    confidence = 0.7  # Base confidence
    if historical_yields:
        confidence += 0.1  # Increase confidence if we have historical data
    if 0.9 <= temperature_factor <= 1.1 and 0.9 <= rainfall_factor <= 1.1:
        confidence += 0.1  # Increase confidence if weather is ideal
    
    return predicted_yield, min(confidence, 1.0)  # Ensure confidence doesn't exceed 1.0

def generate_crop_recommendation(farm, weather_info, historical_crops=None):
    if not weather_info:
        return []
    
    # Basic recommendation logic (you should replace this with your actual logic)
    temp = weather_info.get('main', {}).get('temp', 0)
    humidity = weather_info.get('main', {}).get('humidity', 0)
    
    recommendations = []
    if temp > 25 and humidity > 60:
        recommendations.append({'name': 'Rice', 'predicted_yield': 100})
    elif temp > 20 and humidity > 50:
        recommendations.append({'name': 'Corn', 'predicted_yield': 150})
    else:
        recommendations.append({'name': 'Wheat', 'predicted_yield': 120})
    
    return recommendations
    
