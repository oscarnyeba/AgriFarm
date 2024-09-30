# AgriFarm Management System

## Description
AgriFarm is a Django-based web application for managing farms, tracking weather conditions, and providing crop recommendations based on environmental factors. It allows users to create farms, view weather forecasts, and receive crop recommendations tailored to their farm's location.

## Features
- User authentication (registration and login)
- Admin interface for managing crops
- Farm management (create, edit, delete farms)
- Automatic geolocation for farms
- Real-time weather data integration with 7-day forecast
- Crop recommendations based on weather conditions
- Interactive dashboard with weather details and farm information

## Technologies Used
- Django 3.x
- Python 3.x
- MySQL
- HTML/CSS/JavaScript
- OpenWeatherMap API
- Geopy for coordinate lookup

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/agrifarm.git
   cd agrifarm
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   - Create a MySQL database
   

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser account:
   ```
   python manage.py createsuperuser
   ```
   Follow the prompts to create your admin account.

7. Start the development server:
   ```
   python manage.py runserver
   ```

8. Visit `http://localhost:8000` in your browser

## Environment Variables
Ensure the following environment variables are set in your `.env` file:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to True for development
- `DB_NAME`: Your database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `WEATHER_API_KEY`: Your OpenWeatherMap API key

## Initial Crop Data Setup

To set up the initial crop data for the AgriFarm system, follow these steps:

1. Ensure you have MySQL Workbench installed and connected to your project's database.

2. Open MySQL Workbench and connect to your database.

3. Create a new SQL tab for executing queries.

4. Copy and paste the following SQL query into the new tab:

   ```sql
   INSERT INTO farm_management_crop
    (crop_name, crop_type, growing_season, ideal_temperature_min, ideal_temperature_max, ideal_humidity_min, ideal_humidity_max, ideal_rainfall_min, ideal_rainfall_max)
VALUES
    ('Wheat', 'Grain', 'Winter', 5, 25, 50, 60, 1.50, 3.00),
    ('Rice', 'Grain', 'Monsoon', 20, 35, 60, 80, 3.50, 4.50),
    ('Maize', 'Grain', 'Summer', 15, 30, 50, 70, 2.00, 4.00),
    ('Barley', 'Grain', 'Winter', 7, 24, 50, 70, 1.50, 3.50),
    ('Cotton', 'Fiber', 'Summer', 20, 35, 60, 70, 2.50, 4.50),
    ('Soybean', 'Legume', 'Summer', 20, 30, 60, 80, 3.00, 4.00),
    ('Sorghum', 'Grain', 'Summer', 15, 35, 50, 70, 1.50, 3.50),
    ('Tomato', 'Vegetable', 'Summer', 15, 25, 60, 70, 2.00, 4.00),
    ('Potato', 'Vegetable', 'Spring', 10, 20, 70, 80, 1.00, 3.00),
    ('Carrot', 'Vegetable', 'Winter', 8, 24, 60, 75, 0.50, 2.50),
    ('Cabbage', 'Vegetable', 'Winter', 10, 20, 60, 80, 1.00, 3.00),
    ('Lettuce', 'Vegetable', 'Winter', 5, 20, 60, 75, 0.50, 2.00),
    ('Spinach', 'Leafy', 'Winter', 5, 20, 60, 70, 0.50, 2.00),
    ('Peas', 'Legume', 'Spring', 10, 25, 50, 70, 1.50, 3.00),
    ('Chickpea', 'Legume', 'Winter', 15, 30, 50, 60, 1.00, 3.00),
    ('Onion', 'Vegetable', 'Winter', 10, 30, 60, 80, 1.50, 3.00),
    ('Garlic', 'Vegetable', 'Winter', 10, 25, 60, 80, 1.00, 2.50),
    ('Banana', 'Fruit', 'Tropical', 20, 30, 70, 90, 3.00, 4.50),
    ('Apple', 'Fruit', 'Temperate', 15, 25, 60, 70, 2.00, 4.00),
    ('Grapes', 'Fruit', 'Summer', 20, 30, 60, 80, 2.50, 4.00),
    ('Mango', 'Fruit', 'Summer', 25, 40, 60, 90, 2.50, 4.50),
    ('Orange', 'Fruit', 'Winter', 10, 25, 60, 80, 1.50, 3.00),
    ('Pineapple', 'Fruit', 'Tropical', 20, 30, 70, 90, 3.00, 4.50),
    ('Sugarcane', 'Fiber', 'Summer', 20, 35, 60, 80, 3.50, 4.50),
    ('Tea', 'Beverage', 'Monsoon', 15, 30, 70, 90, 3.00, 4.50),
    ('Coffee', 'Beverage', 'Tropical', 20, 30, 60, 80, 3.00, 4.50),
    ('Cotton', 'Fiber', 'Summer', 25, 35, 60, 80, 2.00, 4.00),
    ('Flax', 'Fiber', 'Spring', 15, 25, 60, 80, 2.50, 4.00),
    ('Alfalfa', 'Legume', 'Spring', 15, 25, 60, 80, 2.50, 4.00),
    ('Sunflower', 'Oilseed', 'Summer', 20, 30, 60, 80, 2.00, 4.00),
    ('Peanut', 'Oilseed', 'Summer', 20, 35, 60, 80, 2.50, 4.50),
    ('Rapeseed', 'Oilseed', 'Winter', 10, 25, 60, 80, 1.50, 3.00),
    ('Oats', 'Grain', 'Spring', 10, 25, 60, 80, 1.50, 3.00),
    ('Millet', 'Grain', 'Summer', 20, 35, 50, 70, 2.00, 4.00),
    ('Mustard', 'Oilseed', 'Winter', 10, 25, 60, 80, 1.00, 3.00),
    ('Cucumber', 'Vegetable', 'Summer', 20, 30, 60, 80, 2.00, 3.50),
    ('Watermelon', 'Fruit', 'Summer', 20, 35, 60, 80, 1.50, 3.00),
    ('Pumpkin', 'Vegetable', 'Autumn', 20, 30, 60, 80, 2.00, 4.00),
    ('Zucchini', 'Vegetable', 'Summer', 20, 30, 60, 80, 2.00, 4.00),
    ('Eggplant', 'Vegetable', 'Summer', 20, 30, 60, 80, 2.00, 4.00),
    ('Pepper', 'Vegetable', 'Summer', 20, 30, 60, 80, 2.00, 4.00),
    ('Strawberry', 'Fruit', 'Spring', 15, 25, 60, 70, 1.50, 3.00),
    ('Blueberry', 'Fruit', 'Summer', 20, 25, 60, 80, 1.50, 3.50),
    ('Raspberry', 'Fruit', 'Summer', 15, 25, 60, 70, 1.50, 3.00),
    ('Coconut', 'Fruit', 'Tropical', 25, 35, 70, 90, 3.00, 4.50),
    ('Papaya', 'Fruit', 'Tropical', 20, 30, 60, 80, 2.50, 0.10),
   ('Avocado', 'Fruit', 'Tropical', 20, 30, 60, 80, 3.00, 1.50);

   ```

5. Execute the query by clicking the lightning bolt icon or pressing Ctrl+Enter (Cmd+Enter on Mac).

6. Verify that the data has been inserted by running a SELECT query:

   ```sql
   SELECT * FROM farm_management_crop;
   ```

   You should see the list of crops you just inserted.

Note: Make sure to adjust the table name (`crops` in this example) and column names to match your actual database schema if they're different.

Important: Before running any SQL queries, especially those that modify data, it's always a good practice to backup your database.

## Usage

1. Admin Setup:
   - Log in to the admin interface at `http://localhost:8000/admin` using your superuser credentials.
   - Add crops through the admin interface if not added initially. These will be used for recommendations.

2. User Registration and Login:
   - Navigate to the registration page and create a new user account.
   - Log in with your new account credentials.

3. Creating a Farm:
   - After logging in, you'll be prompted to create a farm.
   - Enter the farm name and location (city or address)
   - The system will automatically determine the coordinates for the farm.

4. Viewing Farm Details:
   - Click on a farm from your farm list to view its details.
   - The farm detail page displays:
     - Current weather conditions
     - 7-day weather forecast
     - Crop recommendations based on weather data

5. Interacting with the Farm Detail Page:
   - Use the left panel to shuffle through different days of the weather forecast.
   - Edit farm details, including location, using the 'Edit Farm' button.

6. Logging Out:
   - Use the logout button when you're done to securely end your session.

## Troubleshooting
- If you encounter issues with geolocation, ensure you have a stable internet connection and that the address entered is valid.
- For weather data issues, check that your API key is correctly set in the settings file.



## Contact
For any queries or support, please contact Oscar Nyeba at oscarnyeba@gmail.com.