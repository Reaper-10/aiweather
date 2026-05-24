from typing import Final, Dict
import os
from dotenv import load_dotenv
import subprocess

load_dotenv()
MODEL: Final[str] = os.getenv("MODEL", "gpt-4")
OLLAMA_MODEL: Final[str] = os.getenv("OLLAMA_MODEL", "")

# Use local AI for reliable, short, profile-aware responses
def analyze(weather: Dict, prompt: str):
    """Analyze weather data and respond with profile-specific tips"""
    # If configured to use Ollama, delegate the prompt to the local Ollama CLI
    if MODEL == "ollama":
        if not OLLAMA_MODEL:
            raise Exception("OLLAMA_MODEL environment variable not set for Ollama integration")
        try:
            proc = subprocess.run(["ollama", "run", OLLAMA_MODEL, "--prompt", prompt], capture_output=True, text=True, timeout=30)
            if proc.returncode == 0:
                return proc.stdout.strip()
            else:
                raise Exception(proc.stderr.strip() or "ollama run failed")
        except FileNotFoundError:
            raise Exception("ollama CLI not found. Is Ollama installed and on PATH?")
        except subprocess.TimeoutExpired:
            raise Exception("ollama run timed out")

    condition = weather.get("condition", "Unknown").lower()
    temp = weather.get("temp", "N/A")
    city = weather.get("city", "your location")
    humidity = weather.get("humidity", "N/A")
    wind = weather.get("wind", "N/A")
    feels = weather.get("feels", temp)
    forecast = weather.get("forecast", [])
    prompt_lower = prompt.lower()
    
    user_message = ""
    if "user asks:" in prompt_lower:
        user_message = prompt_lower.split("user asks:", 1)[1].strip()

    temp_int = try_parse_int(temp, default=20)
    profile = extract_profile(prompt_lower)
    intent = classify_intent(user_message)

    if intent == "greeting":
        greeting = "Hello! 👋 I'm your AI Weather Assistant."
        if profile:
            greeting += f" I'm analyzing the weather in {city} as a {profile}."
        return f"{greeting} {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "temperature":
        return f"🌡️ Current temperature in {city} is {temp}°C (feels like {feels}°C). {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "rain":
        answer = build_rain_response(city, user_message, condition, forecast, profile, temp_int, temp)
        return answer

    if intent == "humidity":
        return f"💧 Current humidity in {city} is {humidity}%. {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "wind":
        return f"🍃 Wind in {city} is {wind} m/s. {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "pressure":
        return f"📈 Current pressure in {city} is {weather.get('pressure', 'N/A')} hPa. {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "forecast":
        future = select_forecast_day(forecast)
        if future:
            return f"🌅 {future['date']} in {city}: {future['condition']} with highs of {future['temp_max']}°C and lows of {future['temp_min']}°C. {get_profile_advice(profile, future['condition'].lower(), (future['temp_max'] + future['temp_min']) // 2, future['temp_max'])}"
        return f"📅 Forecast unavailable. Current weather: {condition} at {temp}°C. {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "advice":
        return f"💡 Here's your weather advice for {city}: {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "travel":
        return f"🧳 Travel advice for {city}: {get_profile_advice(profile, condition, temp_int, temp)}"

    if intent == "report":
        return build_report(city, condition, temp, feels, humidity, wind, forecast, profile, temp_int)

    return get_profile_advice(profile, condition, temp_int, temp)


def try_parse_int(value, default=20):
    try:
        return int(value) if isinstance(value, str) else value
    except Exception:
        return default


def extract_profile(text: str) -> str:
    profiles = ["farmer", "gym", "student", "traveler", "sports", "office", "rider", "home", "photographer"]
    for profile in profiles:
        if profile in text:
            return profile
    return ""


def classify_intent(message: str) -> str:
    if not message:
        return "general"

    rain_terms = ["rain", "rainfall", "drizzle", "shower", "thunder", "storm", "wet"]
    forecast_terms = ["tomorrow", "forecast", "next day", "weekend", "upcoming"]
    temp_terms = ["temperature", "temp", "hot", "cold", "heat", "chill"]
    humidity_terms = ["humidity", "humid", "dry"]
    travel_terms = ["travel", "commute", "trip", "journey", "drive", "road", "flight", "station"]
    wind_terms = ["wind", "breeze", "gust"]
    pressure_terms = ["pressure", "barometer", "atmosphere"]
    advice_terms = ["advice", "should i", "can i", "recommend", "planning", "plan"]
    report_terms = ["report", "summary", "overview"]
    greeting_terms = ["hello", "hi", "hey", "greetings", "good morning", "good evening"]

    if any(term in message for term in greeting_terms):
        return "greeting"
    if any(term in message for term in rain_terms):
        if any(term in message for term in forecast_terms):
            return "rain"
        return "rain"
    if any(term in message for term in humidity_terms):
        return "humidity"
    if any(term in message for term in wind_terms):
        return "wind"
    if any(term in message for term in pressure_terms):
        return "pressure"
    if any(term in message for term in report_terms):
        return "report"
    if any(term in message for term in travel_terms):
        return "travel"
    if any(term in message for term in advice_terms):
        return "advice"
    if any(term in message for term in temp_terms):
        return "temperature"
    if any(term in message for term in forecast_terms):
        return "forecast"
    return "general"


def select_forecast_day(forecast: list) -> dict:
    if not forecast:
        return None
    if len(forecast) > 1:
        return forecast[1]
    return forecast[0]


def is_rain_condition(condition: str) -> bool:
    return any(keyword in condition for keyword in ["rain", "drizzle", "shower", "storm", "thunder"])


def build_rain_response(city: str, user_message: str, condition: str, forecast: list, profile: str, temp_int: int, temp: str) -> str:
    target = "tomorrow" if "tomorrow" in user_message or "next" in user_message else "today"
    future = select_forecast_day(forecast)
    if future and target == "tomorrow" and len(forecast) > 1:
        future = forecast[1]
    if future and is_rain_condition(future["condition"].lower()):
        response = f"🌧️ Rain is likely in {city} {target}, with {future['condition']} and temperatures from {future['temp_min']}°C to {future['temp_max']}°C."
        response += f" {get_profile_advice(profile, future['condition'].lower(), (future['temp_max'] + future['temp_min']) // 2, future['temp_max'])}"
        return response
    if future:
        response = f"☀️ No significant rain expected in {city} {target}. Forecast shows {future['condition']} with highs around {future['temp_max']}°C."
        response += f" {get_profile_advice(profile, condition, temp_int, temp)}"
        return response
    return f"🌧️ I don't have a forecast available for rain in {city}, but current conditions are {condition} at {temp}°C. {get_profile_advice(profile, condition, temp_int, temp)}"


def build_report(city: str, condition: str, temp: str, feels: str, humidity: str, wind: str, forecast: list, profile: str, temp_int: int) -> str:
    report = (
        f"📊 Weather Report for {city}:\n"
        f"• Temperature: {temp}°C (feels like {feels}°C)\n"
        f"• Condition: {condition.title()}\n"
        f"• Humidity: {humidity}%\n"
        f"• Wind: {wind} m/s"
    )
    future = select_forecast_day(forecast)
    if future:
        report += f"\n• Tomorrow: {future['condition']}, {future['temp_max']}/{future['temp_min']}°C"
    report += f"\n\n💡 {get_profile_advice(profile, condition, temp_int, temp)}"
    return report

def get_profile_advice(profile: str, condition: str, temp_int: int, temp: str) -> str:
    """Get profile-specific weather advice"""
    # Return response based on profile
    if profile == "farmer":
        if "rain" in condition or "drizzle" in condition:
            return "🌾 Great moisture! Monitor drainage to avoid waterlogging."
        elif "clear" in condition or "sunny" in condition or "mainly clear" in condition:
            return f"☀️ Perfect fieldwork weather at {temp}°C. Water your crops well!"
        elif "partly cloudy" in condition or "overcast" in condition:
            return f"🌾 Good working conditions at {temp}°C. Check soil moisture and plan outdoor activities."
        else:
            return f"🌾 Moderate conditions. Check soil moisture before watering."
    
    elif profile == "gym":
        if "rain" in condition or "drizzle" in condition:
            return "💪 Rainy day inside! Hit the gym or do indoor workouts."
        elif temp_int > 28:
            return f"☀️ Too hot ({temp}°C)! Workout early morning or evening instead."
        elif temp_int < 15:
            return f"❄️ Cold at {temp}°C - perfect for intense training!"
        else:
            return f"💪 Great gym weather at {temp}°C! Go crush it!"
    
    elif profile == "student":
        if "rain" in condition or "drizzle" in condition:
            return "📚 Rainy day = perfect study vibes! Stay focused indoors."
        elif "sunny" in condition and temp_int > 25:
            return f"☀️ Too hot ({temp}°C) to go out. Study in AC comfort!"
        else:
            return f"📚 Good study weather! {condition.title()} at {temp}°C."
    
    elif profile == "traveler":
        if "rain" in condition or "drizzle" in condition:
            return "🧳 Grab an umbrella! Rainy day - plan indoor activities."
        elif "sunny" in condition:
            return f"☀️ Perfect travel weather at {temp}°C! Pack sunscreen & explore!"
        else:
            return f"🧳 Good weather for exploring. {condition.title()} at {temp}°C."
    
    elif profile == "sports":
        if "rain" in condition:
            return "🏏 Slippery field! Wear cleats with good grip for safety."
        elif temp_int > 30:
            return f"☀️ Very hot ({temp}°C)! Hydrate frequently during play."
        elif temp_int < 10:
            return f"❄️ Cold at {temp}°C - warm up well before playing!"
        else:
            return f"🏏 Great conditions at {temp}°C! Go play hard!"
    
    elif profile == "office":
        if "rain" in condition:
            return "🧑‍💼 Rainy day - bring an umbrella for commute. WFH if possible!"
        elif "sunny" in condition and temp_int > 30:
            return f"☀️ Hot outside ({temp}°C)! AC at office is better."
        else:
            return f"🧑‍💼 Good work weather at {temp}°C. {condition.title()}."
    
    elif profile == "rider":
        if "rain" in condition or "drizzle" in condition:
            return "🚴 Wet roads! Ride slow, wear reflective gear. Be safe!"
        elif "wind" in condition or "storm" in condition:
            return f"🚴 Windy at {temp}°C! Secure cargo, ride carefully."
        else:
            return f"🚴 Safe riding weather at {temp}°C! Stay hydrated."
    
    elif profile == "home":
        if "rain" in condition:
            return "🏡 Cozy rainy day! Perfect for cooking or family time."
        elif "sunny" in condition and temp_int > 25:
            return f"☀️ Beautiful day at {temp}°C! Open windows, enjoy fresh air."
        else:
            return f"🏡 Comfortable weather at {temp}°C. Relax at home!"
    
    elif profile == "photographer":
        if "sunny" in condition:
            return "📸 Golden hour light! Shoot early morning or late evening."
        elif "cloudy" in condition:
            return "📸 Overcast is perfect! Diffused light for great portraits."
        elif "rain" in condition:
            return "📸 Wet streets = beautiful reflections! Protect your camera."
        else:
            return f"📸 Good light at {temp}°C. Get some great shots!"
    
    # Default response if no profile matched
    if "rain" in condition:
        return f"🌧️ Rainy at {temp}°C. Grab an umbrella!"
    elif temp_int > 30:
        return f"☀️ Hot at {temp}°C! Stay hydrated, wear sunscreen."
    elif temp_int < 10:
        return f"❄️ Cold at {temp}°C! Dress warmly in layers."
    else:
        return f"🌤️ Nice weather at {temp}°C! Enjoy your day!"

def isBye(text: str) -> bool:
    bye_words = ["bye", "goodbye", "goodnight", "see you", "take care", "exit", "quit"]
    return any(word in text.lower() for word in bye_words)