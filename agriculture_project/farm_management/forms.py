from django import forms
from .models import Farm, WeatherData, Recommendation, Profile, Answer
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['farm_name', 'location', 'total_area']

class WeatherDataForm(forms.ModelForm):
    class Meta:
        model = WeatherData
        exclude = ['date'] 
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'datepicker'}),  # Text input to enable datepicker
        }

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['crop', 'date', 'recommendation_text']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    user_type = forms.ChoiceField(choices=Profile.USER_TYPES)

    class Meta:
        model = User
        fields = ['username', 'password', 'user_type']
        
class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        
