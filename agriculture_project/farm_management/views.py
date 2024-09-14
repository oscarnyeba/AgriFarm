from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Farm, Crop, WeatherData, Recommendation
from .forms import FarmForm, WeatherDataForm, RecommendationForm

def farm_list(request):
    farms = Farm.objects.all()
    return render(request, 'farm_management/farm_list.html', {'farms': farms})

def farm_detail(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    weather_data = WeatherData.objects.filter(farm=farm).order_by('-date')[:10]
    recommendations = Recommendation.objects.filter(farm=farm).order_by('-date')[:5]
    context = {
        'farm': farm,
        'weather_data': weather_data,
        'recommendations': recommendations,
    }
    return render(request, 'farm_management/farm_detail.html', context)

def add_farm(request):
    if request.method == 'POST':
        form = FarmForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('farm_list')
    else:
        form = FarmForm()
    return render(request, 'farm_management/farm_form.html', {'form': form})

def add_weather_data(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    if request.method == 'POST':
        form = WeatherDataForm(request.POST)
        if form.is_valid():
            weather_data = form.save(commit=False)
            weather_data.farm = farm
            weather_data.save()
            return redirect('farm_detail', farm_id=farm.id)
    else:
        form = WeatherDataForm()
    return render(request, 'farm_management/weather_data_form.html', {'form': form, 'farm': farm})

def add_recommendation(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    if request.method == 'POST':
        form = RecommendationForm(request.POST)
        if form.is_valid():
            recommendation = form.save(commit=False)
            recommendation.farm = farm
            recommendation.save()
            return redirect('farm_detail', farm_id=farm.id)
    else:
        form = RecommendationForm()
    return render(request, 'farm_management/recommendation_form.html', {'form': form, 'farm': farm})

def farm_list(request):
    query = request.GET.get('q')
    if query:
        farms = Farm.objects.filter(farm_name__icontains=query)  # Filter farms by name
    else:
        farms = Farm.objects.all()  # Show all farms if no search query

    return render(request, 'farm_management/farm_list.html', {'farms': farms})