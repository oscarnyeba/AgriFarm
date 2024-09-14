from django import forms
from .models import Farm, WeatherData, Recommendation

class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['farm_name', 'location', 'total_area']

class WeatherDataForm(forms.ModelForm):
    class Meta:
        model = WeatherData
        fields = ['date', 'temperature', 'humidity', 'rainfall']

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['crop', 'date', 'recommendation_text']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        
