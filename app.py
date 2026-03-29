from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import asyncio
from lib import getweather, analyze, format
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -------- WEATHER API (Open-Meteo - No API Key Required!) --------
# Using Open-Meteo API: https://open-meteo.com/
# Free, no authentication, no rate limits
# Weather codes reference: https://www.weatherapi.com/docs/weather_conditions.csv

WEATHER_CODES = {
    0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Foggy", 51: "Light Drizzle", 53: "Moderate Drizzle",
    55: "Heavy Drizzle", 61: "Slight Rain", 63: "Moderate Rain",
    65: "Heavy Rain", 71: "Slight Snow", 73: "Moderate Snow",
    75: "Heavy Snow", 80: "Slight Rain Showers", 81: "Moderate Showers",
    82: "Heavy Showers", 85: "Slight Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Hail", 99: "Thunderstorm with Hail"
}

def get_real_weather(city):
    """Fetch real-time weather data from Open-Meteo API (Free, No API Key Required)"""
    if not city or city.strip() == "":
        return None
    
    city = city.strip()
    
    try:
        # Step 1: Geocode the city to get coordinates
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=5)
        geo_data = geo_res.json()
        
        if not geo_data.get("results"):
            print(f"Weather API: City '{city}' not found")
            return None
        
        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        city_name = result["name"]
        country = result.get("country", "Unknown")
        
        # Step 2: Get weather for these coordinates (current + daily forecast)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,pressure_msl&daily=temperature_2m_max,temperature_2m_min,weather_code&temperature_unit=celsius&wind_speed_unit=ms&forecast_days=3"
        weather_res = requests.get(weather_url, timeout=5)
        weather_data = weather_res.json()
        
        current = weather_data["current"]
        pressure = int(current.get("pressure_msl", 1013))
        condition = WEATHER_CODES.get(current["weather_code"], "Unknown")
        
        # Get daily forecast
        daily = weather_data.get("daily", {})
        forecast = []
        if daily.get("time"):
            for i in range(min(3, len(daily["time"]))):  # Next 3 days
                forecast.append({
                    "date": daily["time"][i],
                    "temp_max": round(daily["temperature_2m_max"][i]),
                    "temp_min": round(daily["temperature_2m_min"][i]),
                    "condition": WEATHER_CODES.get(daily["weather_code"][i], "Unknown")
                })
        
        return {
            "temp": round(current["temperature_2m"]),
            "humidity": current["relative_humidity_2m"],
            "pressure": pressure,
            "wind": round(current["wind_speed_10m"], 1),
            "feels": round(current["apparent_temperature"]),
            "condition": condition,
            "city": city_name,
            "country": country,
            "forecast": forecast
        }

    except requests.exceptions.Timeout:
        print(f"Weather API timeout for city: {city}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Weather API request error: {e}")
        return None
    except Exception as e:
        print(f"Error parsing weather data: {e}")
        return None
app = Flask(__name__)
app.secret_key = "secret123"

# -------- DB SETUP --------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------- PROFILE DEFINITIONS --------
PROFILE_DESCRIPTIONS = {
    "farmer": "Farmer who depends on weather for crops and livestock",
    "gym": "Fitness enthusiast focused on outdoor and indoor workouts",
    "student": "Student managing studies and campus activities",
    "traveler": "Traveler planning trips and adventures",
    "sports": "Sports player preparing for matches and training",
    "office": "Office worker commuting and managing work schedule",
    "rider": "Delivery rider working outdoors all day",
    "home": "Homemaker managing household and family",
    "photographer": "Photographer planning shoots and locations"
}

def build_weather_prompt(message, profile, weather, city):
    """
    Build an intelligent prompt with weather and profile context.
    Returns personalized tips based on weather conditions and user profile.
    """
    profile_desc = PROFILE_DESCRIPTIONS.get(profile, profile)
    weather_condition = weather.get("condition", "Unknown")
    temp = weather.get("temp", "N/A")
    humidity = weather.get("humidity", "N/A")
    wind = weather.get("wind", "N/A")
    
    # Ensure profile keyword is included in the prompt for proper recognition
    prompt = f"{profile.upper()} in {city} at {temp}C with {weather_condition} conditions. User asks: {message}"
    return prompt

# -------- SIGNUP --------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = False
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if not user or not pwd:
            error = True
        elif len(pwd) < 4:
            error = True  # Password too short
        else:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()

            try:
                c.execute("INSERT INTO users VALUES (?, ?)", (user, pwd))
                conn.commit()
                conn.close()
                return redirect("/")  # Redirect to login after successful signup
            except:
                error = True  # User already exists

    return render_template("signup.html", error=error)

# -------- LOGIN --------
@app.route("/", methods=["GET", "POST"])
def login():
    error = False
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error = True
        else:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = c.fetchone()
            conn.close()

            if result and result[0] == password:
                session["user"] = username
                return redirect("/dashboard")
            else:
                error = True

    return render_template("login.html", error=error)
# -------- DASHBOARD --------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    # Get or set profile from session/form
    if request.method == "POST" and "profile" in request.form:
        session["profile"] = request.form.get("profile", "student")
    
    user_profile = session.get("profile", "student")
    
    weather = None
    # Preserve location: only update if explicitly provided in form, otherwise use session
    if request.method == "POST" and "location" in request.form:
        location = request.form.get("location")
        session["location"] = location
    else:
        location = session.get("location", "Bangalore")
    
    error_message = ""

    if location:
        weather = get_real_weather(location)
        if weather is None:
            error_message = f"Could not fetch weather for '{location}'. Please check the city name."
            weather = {
                "temp": "N/A",
                "humidity": "N/A",
                "pressure": "N/A",
                "wind": "N/A",
                "feels": "N/A",
                "condition": "Unknown",
                "city": location,
                "country": "",
                "forecast": []
            }
    else:
        # Fallback if API fails
        weather = {
            "temp": "N/A",
            "humidity": "N/A",
            "pressure": "N/A",
            "wind": "N/A",
            "feels": "N/A",
            "condition": "Clouds",
            "city": "Bangalore",
            "country": "IN",
            "forecast": []
        }

    return render_template(
        "dashboard.html",
        weather=weather,
        location=location,
        user=session.get("user", "User"),
        profile=user_profile,
        profiles=PROFILE_DESCRIPTIONS.keys(),
        error=error_message,
        chat_history=[]
    )
# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------- CHAT --------
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return redirect("/")

    msg = request.form.get("message", "")
    user_profile = session.get("profile", "student")
    location = session.get("location", "Bangalore")
    
    # Get current weather
    weather = get_real_weather(location)
    if weather is None:
        weather = {
            "temp": "N/A",
            "humidity": "N/A",
            "pressure": "N/A",
            "wind": "N/A",
            "feels": "N/A",
            "condition": "Unknown",
            "city": location,
            "country": "",
            "forecast": []
        }
    
    # Build intelligent prompt with weather and profile context
    prompt = build_weather_prompt(msg, user_profile, weather, location)
    response = format(analyze(weather, prompt))

    # Return JSON response for AJAX requests
    return jsonify({"response": response})

app.run(debug=True)