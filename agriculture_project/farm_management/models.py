from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.urls import reverse


class SoilTexture(models.TextChoices):
    SANDY = 'Sandy', 'Sandy'
    LOAMY = 'Loamy', 'Loamy'
    CLAY = 'Clay', 'Clay'
    SILTY = 'Silty', 'Silty'
    PEATY = 'Peaty', 'Peaty'
    CHALKY = 'Chalky', 'Chalky'
    ANY = 'Any', 'Any'
class Soil(models.Model):
    farm = models.OneToOneField('Farm', on_delete=models.CASCADE, related_name='soil')
    ph_level = models.FloatField()
    nitrogen_level = models.FloatField()
    phosphorus_level = models.FloatField()
    potassium_level = models.FloatField()
    texture = models.CharField(max_length=50, choices=[
        ('Sandy', 'Sandy'),
        ('Loamy', 'Loamy'),
        ('Clay', 'Clay'),
        ('Silty', 'Silty'),
        ('Peaty', 'Peaty'),
        ('Chalky', 'Chalky'),
    ], default='Loamy')

    class Meta:
        db_table = 'soil_table'
        ordering = ['ph_level']

    def __str__(self):
        return f"Soil conditions for {self.farm.farm_name}"

class Farm(models.Model):
    farm_name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255)  # City name or manual input for OpenWeather
    latitude = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    total_area = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms') 
    def __str__(self):
        return self.farm_name
    
    class Meta:
        verbose_name = 'Farm'
        verbose_name_plural = 'Farms'

class Crop(models.Model):
    crop_name = models.CharField(max_length=50, help_text="Enter the name of the crop.")
    crop_type = models.CharField(max_length=50, help_text="Specify the type of crop.")
    growing_season = models.CharField(max_length=50, choices=[
        ('Spring', 'Spring'),
        ('Summer', 'Summer'),
        ('Autumn', 'Autumn'),
        ('Winter', 'Winter'),
    ], help_text="Define the growing season of the crop.")
    ideal_temperature_min = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(-50), MaxValueValidator(50)], help_text="Enter the minimum ideal temperature for the crop.")
    ideal_temperature_max = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(-50), MaxValueValidator(50)], help_text="Enter the maximum ideal temperature for the crop.")
    ideal_humidity_min = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Enter the minimum ideal humidity for the crop.")
    ideal_humidity_max = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Enter the maximum ideal humidity for the crop.")
    ideal_rainfall_min = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(200)], help_text="Enter the minimum ideal rainfall for the crop.")
    ideal_rainfall_max = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(200)], help_text="Enter the maximum ideal rainfall for the crop.")
    preferred_soil_texture = models.CharField(max_length=50, choices=SoilTexture.choices, default=SoilTexture.ANY, help_text="Select the preferred soil texture for the crop.")

    class Meta:
        verbose_name = 'Crop'
        verbose_name_plural = 'Crops'

    def __str__(self):
        return self.crop_name

class WeatherData(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    temperature = models.FloatField()
    humidity = models.FloatField()
    rainfall = models.FloatField()

    def __str__(self):
        return f"{self.farm.farm_name} - {self.date}"

    class Meta:
        unique_together = ('farm', 'date')
        verbose_name = 'Weather Data'
        verbose_name_plural = 'Weather Data'

    def get_absolute_url(self):
        return reverse('weather_data_detail', args=[str(self.id)])

class Recommendation(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    date = models.DateField()
    recommendation_text = models.TextField()

    def __str__(self):
        return f"{self.farm.farm_name} - {self.crop.crop_name} - {self.date}"

class Profile(models.Model):
    USER_TYPES = (
        (1, 'Farmer'),
        (2, 'Expert'),
    )
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    user_type = models.IntegerField(choices=USER_TYPES)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

    def __repr__(self):
        return f"Profile(user={self.user.username}, user_type={self.user_type})"

    class Meta:
        ordering = ['user__username']
        verbose_name = 'User Profile'

    
