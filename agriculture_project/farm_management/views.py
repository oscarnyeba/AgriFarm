from django.db import transaction
from django.db.models import Q
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.decorators import login_required
from .decorators import farm_owner_required
from django.urls import reverse
from .models import Farm, Crop, WeatherData, Recommendation, Profile, User,Question, Answer
from .forms import FarmForm, WeatherDataForm, RecommendationForm, RegistrationForm, AnswerForm
from django.conf import settings
import requests
import logging
from datetime import datetime, timedelta
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect 
from decimal import Decimal



#registration view
def register(request):
    form = RegistrationForm() 
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['username']
            user.save()
            
            # Create Profile
            Profile.objects.create(
                user=user,
                user_type=form.cleaned_data['user_type']
            )

            # Log registration event
            logging.info(f"User registered: {user.username}")

            # Auto-login after registration
            login(request, user)
          # Redirect based on user type
            profile = Profile.objects.get(user=user)
            if profile.user_type == 1:  # Farmer
                return redirect(reverse('farm_list'))
            elif profile.user_type == 2:  # Expert
                return redirect('expert_profile')
    
    return render(request, 'registration/register.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('login')
#login view
@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                try:
                    profile = Profile.objects.get(user=user)
                    # Redirect based on user type
                    if profile.user_type == 1:  # Farmer
                        return redirect('farm_list')
                    elif profile.user_type == 2:  # Expert
                        return redirect('expert_profile')
                except Profile.DoesNotExist:
                    logging.error(f"Profile for user {user.username} does not exist.")
                    form.add_error(None, "Profile does not exist.")
            else:
                form.add_error(None, "Invalid username or password.")
        else:
            form.add_error(None, "Invalid form submission.")
    elif request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.user_type == 1:  # Farmer
                return redirect('farmer_profile')
            elif profile.user_type == 2:  # Expert
                return redirect('expert_profile')
        except Profile.DoesNotExist:
            logging.error(f"Profile for user {request.user.username} does not exist.")
            return redirect('login')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})

# ** Farmer Profile Page **
@login_required
def farmer_profile(request):
    """
    Farmer's profile page with their details (name, photo, farms).
    """
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 1:  # Only Farmers can access this page
        return redirect('login')
    
    farms = Farm.objects.filter(user=request.user)
    return render(request, 'farm_management/farm_list.html', {
        'profile': profile,
        'farms': farms,
    })
    
# ** Expert Profile Page **
@login_required
def expert_profile(request):
    """
    Expert's profile page with unanswered and answered questions.
    """
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 2:  # Only Experts can access this page
        return redirect('login')

    answered_questions = Question.objects.filter(response__isnull=False)
    unanswered_questions = Question.objects.filter(response__isnull=True)

    return render(request, 'farm_management/expert_profile.html', {
        'answered_questions': answered_questions,
        'unanswered_questions': unanswered_questions
    })

# ** Farm List for Farmers **
@login_required
def farm_list_view(request):
    query = request.GET.get('q', '') 
    farms = Farm.objects.filter(user=request.user)
    if query:
        farms = farms.filter(farm_name__icontains=query)
    
    paginator = Paginator(farms, 10)  # Show 10 farms per page
    page = request.GET.get('page')
    try:
        farms = paginator.page(page)
    except PageNotAnInteger:
        farms = paginator.page(1)
    except EmptyPage:
        farms = paginator.page(paginator.num_pages)

    return render(request, 'farm_management/farm_list.html', {'farms': farms, 'query': query})

@login_required
def generate_crop_recommendation(farm, weather_info):
    """
    Generate crop recommendations based on current weather data.
    """
    try:
        # If weather data is unavailable, return an empty list
        if not weather_info or any(value == 'N/A' for value in weather_info.values()):
            logging.warning('Weather data is unavailable or contains N/A values.')
            return []

        # Convert weather data to Decimal for comparison
        current_temperature = Decimal(weather_info['temperature'])
        current_humidity = Decimal(weather_info['humidity'])
        current_rainfall = Decimal(weather_info['rainfall'])

        # Filter crops based on the ideal conditions using Q objects
        recommended_crops = Crop.objects.filter(
            Q(ideal_temperature_min__lte=current_temperature) &
            Q(ideal_temperature_max__gte=current_temperature) &
            Q(ideal_humidity_min__lte=current_humidity) &
            Q(ideal_humidity_max__gte=current_humidity) &
            Q(ideal_rainfall_min__lte=current_rainfall) &
            Q(ideal_rainfall_max__gte=current_rainfall)
        )

        return recommended_crops
    except (ValueError, Crop.DoesNotExist) as e:
        logging.error(f"Error in generating crop recommendation: {e}")
        return []


@farm_owner_required
@login_required
def farm_detail(request, farm_id):
    logging.debug(f"Requesting farm detail for farm_id: {farm_id} and user: {request.user.username}")
    farm = get_object_or_404(Farm.objects.prefetch_related('weatherdata_set'), id=farm_id, user=request.user)
    logging.debug(f"Farm Owner: {farm.user.username}")
    today = datetime.now().date()
    def fetch_or_update_weather_data(farm, date):
        weather_data_today = WeatherData.objects.filter(farm=farm, date=date).first()

        if not weather_data_today:
            try:
                weather_info = fetch_weather_data(farm.location, None)  # Fetch current weather from API
                if weather_info:
                    with transaction.atomic():
                        weather_data_today, created = WeatherData.objects.update_or_create(
                            farm=farm,
                            date=date,
                            defaults={
                                'temperature': weather_info['temperature'],
                                'humidity': weather_info['humidity'],
                                'rainfall': weather_info['rainfall'],
                            }
                        )
            except Exception as e:
                logging.error(f"Error fetching weather data: {e}")

        return weather_data_today

    weather_data_today = fetch_or_update_weather_data(farm, today)

    weather_history = farm.weatherdata_set.filter(date__lt=today).order_by('-date')[:10]

    weather_info = {
        'temperature': weather_data_today.temperature if weather_data_today else None,
        'humidity': weather_data_today.humidity if weather_data_today else None,
        'rainfall': weather_data_today.rainfall if weather_data_today else None
    }
    soil_info = fetch_soil_data(farm)  # Use farm's latitude and longitude

    recommendations = generate_crop_recommendation(farm, weather_info)
    context = {
        'farm': farm,
        'weather_info': weather_data_today,
        'weather_data': weather_history,
        'recommendations': recommendations,
        'soil_info': soil_info,
    }
    return render(request, 'farm_management/farm_detail.html', context)

# ** Restrict Farm Creation to Farmers Only **
@login_required
@csrf_protect
def add_farm(request):
    #Only farmers can add farms. This function handles farm creation.
    
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 1:  # Only Farmers can add farms
        return redirect('login')

    if request.method == 'POST':
        form = FarmForm(request.POST)
        try:
            if form.is_valid():
                location = form.cleaned_data['location']  # Get the location from the form
                latitude, longitude = get_lat_long(location)  # Get lat/long from the location
                if latitude is None or longitude is None:
                    # Handle the case where geocoding fails
                    logging.error("Geocoding failed for location: {}".format(location))
                    form.add_error('location', 'Unable to fetch latitude and longitude for this location.')
                    return render(request, 'farm_management/farm_form.html', {'form': form})

                with transaction.atomic():
                    farm = form.save(commit=False)
                    farm.user = request.user  # Use user instead of owner
                    farm.latitude = latitude  # Set latitude
                    farm.longitude = longitude  # Set longitude
                    farm.save()  # Save the farm instance

                return redirect(reverse('farm_list'))
        except Exception as e:
            logging.error(f"An error occurred while saving the form: {e}")
    else:
        form = FarmForm()
    return render(request, 'farm_management/farm_form.html', {'form': form})

@login_required
def add_weather_data(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    weather_info = None

    if request.method == 'POST':
        form = WeatherDataForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['date']
             # Use get_or_create to fetch or create weather data for the selected date
            weather_data, created = WeatherData.objects.get_or_create(farm=farm, date=selected_date).first()
            if created:
                # If created, fetch weather from the API for the selected date
                weather_info = fetch_weather_data(farm.location, selected_date)

            if weather_info:
                weather_data.temperature = weather_info.get('temperature',0)
                weather_data.humidity = weather_info.get('humidity',0)
                weather_data.rainfall = weather_info.get('rainfall',0)
                weather_data.save()
            else:
                form.add_error(None, 'Failed to fetch weather data from the API')  # Custom error message
        else:
            form.add_error(None, f"Weather data for {selected_date} already exists.")
    else:
        form = WeatherDataForm()


    return render(request, 'farm_management/weather_data_form.html', {
        'form': form,
        'farm': farm,
        'weather_info': weather_info  # Pass the fetched weather info to the template
    })

def fetch_weather_data(location, date=None):
    """
    Function to fetch weather data from OpenWeather based on farm location (city name or coordinates)
    """
    if not location or not isinstance(location, str):
        logging.error("Invalid location provided.")
        return None

    logging.info(f"Fetching weather data for {location} on {date}")

    try:
        api_key = settings.WEATHER_API_KEY
        api_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"

        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        logging.info(f'Weather data fetched {weather_data}')
        temperature = weather_data.get('main', {}).get('temp', 'N/A')  
        humidity = weather_data.get('main', {}).get('humidity', 'N/A')  
        rainfall = weather_data.get('rain', {}).get('1h', 0) 

        return {
            'temperature': temperature,
            'humidity': humidity,
            'rainfall': rainfall
            }
    except requests.exceptions.RequestException as e:
        logging.exception(f"Error occurred during API call: {e}")
        return None
    
@login_required
def ask_expert_view(request):
    answered_questions = Question.objects.filter(response__isnull=False)
    unanswered_questions = Question.objects.filter(response__isnull=True)

    context = {
        'answered_questions': answered_questions,
        'unanswered_questions': unanswered_questions
    }

    return render(request, 'farm_management/ask_expert.html', context)

# ** Expert Answers Questions **
@login_required
def answer_question_view(request, question_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != 2:  # Only Experts can answer questions
        return redirect('login')
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.expert = request.user
            answer.save()

            # Redirect back to the expert_profile after answering
            return redirect('expert_profile')
    else:
        form = AnswerForm()

    return render(request, 'ask_expert/answer_question.html', {'form': form, 'question': question})

@login_required
def edit_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)

    # Ensure that only the farm owner can edit it
    if request.user != farm.user:
        return redirect('farm_list')

    if request.method == 'POST':
        form = FarmForm(request.POST, instance=farm)
        if form.is_valid():
            form.save()
            return redirect('farm_detail', farm_id=farm.id)
    else:
        form = FarmForm(instance=farm)  # Pre-fill the form with existing farm data

    return render(request, 'farm_management/edit_farm.html', {'form': form, 'farm': farm})

def fetch_soil_data(farm):
    latitude = farm.latitude
    longitude = farm.longitude

    if latitude is None or longitude is None:
        logging.error("Invalid farm location: Latitude or Longitude is None")
        return None  # Handle this case as needed

    api_url = f"https://rest.soilgrids.org/query?lon={longitude}&lat={latitude}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad responses
        soil_data = response.json()
        return soil_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching soil data: {e}")
        return None

def get_lat_long(location):
    api_key = 'fUGmuIV8sR29zXoZIeku'  # Replace with your actual MapTiler API key
    url = f'https://api.maptiler.com/geocoding/{location}.json?key={api_key}'
    
    response = requests.get(url)
    
    if response.status_code == 200:
        results = response.json()
        if results['features']:
            lat = results['features'][0]['geometry']['coordinates'][1]  # Latitude
            lng = results['features'][0]['geometry']['coordinates'][0]  # Longitude
            return lat, lng
    return None, None 

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        return redirect('farm_list')  # Redirect back to the profile page
    return render(request, 'farm_management/edit_profile.html', {'user': user})
