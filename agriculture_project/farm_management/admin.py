from django.contrib import admin
from .models import Farm, Crop, WeatherData, Recommendation

admin.site.register(Farm)
admin.site.register(Crop)
admin.site.register(WeatherData)
admin.site.register(Recommendation)
