from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from django.utils import timezone



class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_area = models.FloatField(default=0)  # Add total_area field
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    crops = models.ManyToManyField('Crop', related_name='farms', blank=True)

    def __str__(self):
        return self.name

class Crop(models.Model):
    crop_name = models.CharField(max_length=50, help_text="Enter the name of the crop.")
    crop_type = models.CharField(max_length=50, help_text="Specify the type of crop.")
    growing_season = models.CharField(max_length=50, choices=[
        ('Spring', 'Spring'),
        ('Summer', 'Summer'),
        ('Autumn', 'Autumn'),
        ('Winter', 'Winter'),
    ], help_text="Define the growing season of the crop.")
    ideal_temperature_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(-50), MaxValueValidator(50)],
        help_text="Enter the minimum ideal temperature for the crop."
    )
    ideal_temperature_max = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(-50), MaxValueValidator(50)],
        help_text="Enter the maximum ideal temperature for the crop."
    )
    ideal_humidity_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Enter the minimum ideal humidity for the crop."
    )
    ideal_humidity_max = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Enter the maximum ideal humidity for the crop."
    )
    ideal_rainfall_min = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        help_text="Enter the minimum ideal rainfall for the crop."
    )
    ideal_rainfall_max = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        help_text="Enter the maximum ideal rainfall for the crop."
    )
  

    class Meta:
        verbose_name = 'Crop'
        verbose_name_plural = 'Crops'

    def __str__(self):
        return self.crop_name

# ** Weather Data Model **
class WeatherData(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    date = models.DateField()
    temperature = models.FloatField(default=0.0)
    feels_like = models.FloatField(default=0.0)
    temp_min = models.FloatField(default=0.0)
    temp_max = models.FloatField(default=0.0)
    pressure = models.IntegerField(default=1013)  # Standard sea level pressure
    humidity = models.IntegerField(default=50)  # Average humidity
    visibility = models.IntegerField(default=10000)  # 10 km, good visibility
    wind_speed = models.FloatField(default=0.0)
    wind_direction = models.IntegerField(default=0)
    wind_gust = models.FloatField(null=True, blank=True)
    cloudiness = models.IntegerField(default=0)
    rainfall = models.FloatField(default=0.0)
    weather_main = models.CharField(max_length=100, default='Clear')
    weather_description = models.CharField(max_length=200, default='Clear sky')
    weather_icon = models.CharField(max_length=10, default='01d')

    class Meta:
        unique_together = ('farm', 'date')

    def __str__(self):
        return f"{self.farm.name} - {self.date}"

    def get_absolute_url(self):
        return reverse('weather_data_detail', args=[str(self.id)])


class Recommendation(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    date = models.DateField()
    recommendation_text = models.TextField()

    def __str__(self):
        return f"{self.farm.name} - {self.crop.crop_name} - {self.date}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Assuming you added a new field, for example:
    # new_field = models.CharField(max_length=100, default='Some Default Value')
    
    # Add any other fields you need for the profile

    def __str__(self):
        return self.user.username

    def __repr__(self):
        return f"Profile(user={self.user.username})"

    class Meta:
        ordering = ['user__username']
        verbose_name = 'User Profile'
    


class WeatherForecast(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_forecasts')
    date = models.DateField()
    temperature_max = models.FloatField()
    temperature_min = models.FloatField()
    rainfall = models.FloatField()
    humidity = models.FloatField()

    def __str__(self):
        return f"Forecast for {self.farm.farm_name} on {self.date}"

    class Meta:
        unique_together = ('farm', 'date')
        ordering = ['date']

class CropIdealConditions(models.Model):
    crop = models.OneToOneField(Crop, on_delete=models.CASCADE, related_name='ideal_conditions')
    ideal_temperature_min = models.FloatField()
    ideal_temperature_max = models.FloatField()
    ideal_rainfall_min = models.FloatField()
    ideal_rainfall_max = models.FloatField()
    ideal_humidity_min = models.FloatField()
    ideal_humidity_max = models.FloatField()

    def __str__(self):
        return f"Ideal conditions for {self.crop.crop_name}"

class WeatherImpact(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_impacts')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    date = models.DateField()
    impact_description = models.TextField()

    def __str__(self):
        return f"Impact on {self.crop.crop_name} at {self.farm.farm_name} on {self.date}"

    class Meta:
        unique_together = ('farm', 'crop', 'date')
        ordering = ['date']




