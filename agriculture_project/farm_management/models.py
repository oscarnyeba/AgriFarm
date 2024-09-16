from django.db import models

class Farm(models.Model):
    farm_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)  # City name or manual input for OpenWeather
    latitude = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    total_area = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return self.farm_name

class Crop(models.Model):
    crop_name = models.CharField(max_length=50)
    crop_type = models.CharField(max_length=50)
    growing_season = models.CharField(max_length=50)
    ideal_temperature_min = models.DecimalField(max_digits=5, decimal_places=2, default = 0)
    ideal_temperature_max = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ideal_humidity_min = models.DecimalField(max_digits=5, decimal_places=2, default =0)
    ideal_humidity_max = models.DecimalField(max_digits=5, decimal_places=2, default =0)
    ideal_rainfall_min = models.DecimalField(max_digits=5, decimal_places=2, default =0)
    ideal_rainfall_max = models.DecimalField(max_digits=5, decimal_places=2, default =0)

    def __str__(self):
        return self.crop_name

class WeatherData(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    date = models.DateField()
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.DecimalField(max_digits=5, decimal_places=2)
    rainfall = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.farm.farm_name} - {self.date}"

class Recommendation(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    date = models.DateField()
    recommendation_text = models.TextField()

    def __str__(self):
        return f"{self.farm.farm_name} - {self.crop.crop_name} - {self.date}"
    
class Soil(models.Model):
    farm = models.OneToOneField(Farm, on_delete=models.CASCADE)
    ph_level = models.DecimalField(max_digits=4, decimal_places=2)
    nitrogen_level = models.DecimalField(max_digits=5, decimal_places=2)
    phosphorus_level = models.DecimalField(max_digits=5, decimal_places=2)
    potassium_level = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"Soil conditions for {self.farm.farm_name}"

