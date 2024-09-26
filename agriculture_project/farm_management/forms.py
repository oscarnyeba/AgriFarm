from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Farm, WeatherData, Recommendation

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help_text
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors:
            return cleaned_data

        if 'password1' in self.errors:
            self.fields['password1'].widget.attrs.update({'class': 'error'})
            self.fields['password2'].widget.attrs.update({'class': 'error'})

        return cleaned_data

class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['farm_name', 'location', 'latitude', 'longitude']

class WeatherDataForm(forms.ModelForm):
    class Meta:
        model = WeatherData
        fields = [
            'temperature', 'feels_like', 'temp_min', 'temp_max', 'pressure',
            'humidity', 'visibility', 'wind_speed', 'wind_direction', 'wind_gust',
            'cloudiness', 'rainfall', 'weather_main', 'weather_description', 'weather_icon'
        ]

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['recommendation_text']
