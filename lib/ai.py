from typing import Final, Dict
import os
from dotenv import load_dotenv

load_dotenv()
MODEL: Final[str] = os.getenv("MODEL", "gpt-4")

# Use local AI for reliable, short, profile-aware responses
def analyze(weather: Dict, prompt: str):
    """Analyze weather data and respond with profile-specific tips"""
    condition = weather.get("condition", "Unknown").lower()
    temp = weather.get("temp", "N/A")
    city = weather.get("city", "your location")
    forecast = weather.get("forecast", [])
    prompt_lower = prompt.lower()
    
    # Extract user message from prompt
    user_message = ""
    if "User asks:" in prompt:
        user_message = prompt.split("User asks:", 1)[1].strip().lower()
    
    # Convert temperature to int for comparisons
    try:
        temp_int = int(temp) if isinstance(temp, str) else temp
    except:
        temp_int = 20  # Default to moderate temperature
    
    # Extract profile from prompt
    profile = ""
    if "farmer" in prompt_lower:
        profile = "farmer"
    elif "gym" in prompt_lower:
        profile = "gym"
    elif "student" in prompt_lower:
        profile = "student"
    elif "traveler" in prompt_lower:
        profile = "traveler"
    elif "sports" in prompt_lower:
        profile = "sports"
    elif "office" in prompt_lower:
        profile = "office"
    elif "rider" in prompt_lower:
        profile = "rider"
    elif "home" in prompt_lower:
        profile = "home"
    elif "photographer" in prompt_lower:
        profile = "photographer"
    
    # Handle specific queries first
    if any(word in user_message for word in ["hello", "hi", "hey", "greetings"]):
        greeting = "Hello! 👋 I'm your AI Weather Assistant."
        if profile:
            greeting += f" I'm analyzing the weather in {city} as a {profile}."
        return f"{greeting} {get_profile_advice(profile, condition, temp_int, temp)}"
    
    elif "temperature" in user_message or "temp" in user_message or "hot" in user_message or "cold" in user_message:
        return f"🌡️ Current temperature in {city} is {temp}°C (feels like {weather.get('feels', temp)}°C). {get_profile_advice(profile, condition, temp_int, temp)}"
    
    elif "tomorrow" in user_message or "forecast" in user_message:
        if forecast and len(forecast) > 0:
            tomorrow = forecast[0]
            return f"🌅 Tomorrow in {city}: {tomorrow['condition']} with highs of {tomorrow['temp_max']}°C and lows of {tomorrow['temp_min']}°C. {get_profile_advice(profile, tomorrow['condition'].lower(), (tomorrow['temp_max'] + tomorrow['temp_min']) // 2, tomorrow['temp_max'])}"
        else:
            return f"📅 Forecast unavailable. Current weather: {condition} at {temp}°C. {get_profile_advice(profile, condition, temp_int, temp)}"
    
    elif "weather report" in user_message or "report" in user_message or "summary" in user_message:
        humidity = weather.get("humidity", "N/A")
        wind = weather.get("wind", "N/A")
        report = f"📊 Weather Report for {city}:\n• Temperature: {temp}°C (feels {weather.get('feels', temp)}°C)\n• Condition: {weather.get('condition', 'Unknown')}\n• Humidity: {humidity}%\n• Wind: {wind} m/s"
        if forecast and len(forecast) > 1:
            report += f"\n• Tomorrow: {forecast[0]['condition']}, {forecast[0]['temp_max']}/{forecast[0]['temp_min']}°C"
        return f"{report}\n\n💡 {get_profile_advice(profile, condition, temp_int, temp)}"
    
    # Default: provide profile-specific advice
    return get_profile_advice(profile, condition, temp_int, temp)

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