from typing import Final, Dict
import os
from dotenv import load_dotenv

load_dotenv()
MODEL: Final[str] = os.getenv("MODEL", "gpt-4")

# Try to use smartfunc/llm backend, fall back to local AI if unavailable
try:
    from smartfunc import backend
    
    ai: Final[object] = backend(MODEL, 
        system="""
        You are an AI agent for a weather API. Provide short, friendly, and to-the-point responses. 
        Avoid unnecessary words. Do not use Markdown or any formatting—plain text only. 
        Always keep replies as brief and clear as possible. 
        Follow this style strictly.
        """)

    @ai
    def analyze(weather: Dict, prompt: str):
        """Analyze the weather data and respond to the user's question with helpful tips"""
        ...
        
except Exception as e:
    print(f"\n[INFO] Using local AI response engine (external AI not configured)\n")
    
    # Fallback: Simple local AI responses based on weather and profile
    def analyze(weather: Dict, prompt: str):
        """Local AI response generator without external dependencies"""
        
        # Extract weather info
        condition = weather.get("condition", "Unknown").lower()
        temp = weather.get("temp", "N/A")
        humidity = weather.get("humidity", "N/A")
        wind = weather.get("wind", "N/A")
        city = weather.get("city", "your location")
        
        # Generate weather-specific, profile-specific response
        response = generate_local_response(condition, temp, humidity, wind, city, prompt)
        return response

def generate_local_response(condition, temp, humidity, wind, city, prompt):
    """Generate smart responses based on weather and profile without external AI"""
    
    prompt_lower = prompt.lower()
    
    # Profile-specific responses
    if "farmer" in prompt_lower or "farming" in prompt_lower or "crop" in prompt_lower:
        if "rain" in condition or "drizzle" in condition:
            return "Great weather for crop irrigation! Make sure fields don't get waterlogged. Ideal conditions for planting if soil is ready."
        elif "clear" in condition or "sunny" in condition:
            return f"Perfect farming weather at {temp}C in {city}. Water crops well and monitor soil moisture. Apply sunscreen for yourself!"
        elif "cloudy" in condition:
            return "Good for avoiding sun damage. Ideal time for general farm maintenance and weeding without heat stress."
        else:
            return f"Check soil conditions before working. Temperature is {temp}C. Monitor crops for any weather stress."
    
    elif "gym" in prompt_lower or "fitness" in prompt_lower or "workout" in prompt_lower or "exercise" in prompt_lower:
        if "rain" in condition:
            return f"Indoor workout day! Perfect for gym/yoga at {temp}C. Cooler temps make cardio easier. Stay motivated!"
        elif "sunny" in condition or "clear" in condition:
            return f"Excellent outdoor running/cycling weather at {temp}C! Stay hydrated and wear sunscreen. Amazing energy today!"
        elif isinstance(temp, (int, float)) and temp > 25:
            return f"Hot at {temp}C - Early morning/evening outdoor workouts recommended. Indoor AC workouts are ideal today."
        else:
            return f"Good conditions for outdoor fitness at {temp}C. Remember to warm up properly before exercise!"
    
    elif "student" in prompt_lower or "study" in prompt_lower or "exam" in prompt_lower:
        if "rain" in condition:
            return f"Perfect study day indoors at {temp}C. Cool weather helps concentration. Complete those assignments!"
        elif "sunny" in condition or "clear" in condition:
            return f"Great outdoor study weather at {temp}C! Library, park, or campus courtyard would be ideal."
        else:
            return f"Good weather for campus activities at {temp}C. Comfortable conditions for group study sessions!"
    
    elif "traveler" in prompt_lower or "travel" in prompt_lower or "trip" in prompt_lower or "tour" in prompt_lower:
        if "rain" in condition:
            return f"Rainy in {city} at {temp}C - Pack umbrella! Good for indoor attractions and museums."
        elif "sunny" in condition or "clear" in condition:
            return f"Perfect travel weather in {city} at {temp}C! Book outdoor tours and hiking. Don't forget sunscreen!"
        else:
            return f"Good conditions for exploring {city} at {temp}C. Comfortable for walking tours!"
    
    elif "sports" in prompt_lower or "player" in prompt_lower or "match" in prompt_lower or "game" in prompt_lower:
        if "rain" in condition:
            return f"Training on wet surfaces at {temp}C - practice grip and balance. Stay safe!"
        elif "sunny" in condition or "clear" in condition:
            return f"Perfect match conditions at {temp}C in {city}! Good visibility and high energy. Prepare mentally!"
        else:
            return f"Ideal training conditions at {temp}C. Comfortable weather for practice!"
    
    elif "office" in prompt_lower or "work" in prompt_lower or "job" in prompt_lower or "commute" in prompt_lower:
        if "rain" in condition:
            return f"Rainy in {city} - Consider public transport. Work from home option available today."
        elif "sunny" in condition or "clear" in condition:
            return f"Beautiful weather at {temp}C! Plan outdoor lunch breaks. Extra energy for meetings!"
        else:
            return f"Normal workday weather at {temp}C. Good conditions for commuting."
    
    elif "rider" in prompt_lower or "delivery" in prompt_lower or "ride" in prompt_lower or "bike" in prompt_lower:
        if "rain" in condition:
            return f"Slippery roads at {temp}C - Extra caution needed. Poor visibility increases delivery time. Stay safe!"
        elif "sunny" in condition or "clear" in condition:
            return f"Ideal delivery weather at {temp}C! Maximum visibility and comfort. Safe riding conditions!"
        elif isinstance(temp, (int, float)) and temp > 30:
            return f"Hot at {temp}C - Hydrate frequently. Sunscreen essential. Take shade breaks when you can."
        else:
            return f"Good riding conditions at {temp}C. Safe visibility for deliveries!"
    
    elif "home" in prompt_lower or "house" in prompt_lower or "family" in prompt_lower or "cooking" in prompt_lower:
        if "rain" in condition:
            return f"Perfect for indoor cleaning and organizing at {temp}C. Good for cooking and baking projects!"
        elif "sunny" in condition or "clear" in condition:
            return f"Great weather for laundry and yard work at {temp}C! Fresh air activities recommended."
        else:
            return f"Cozy weather at {temp}C. Good for meal planning and family activities!"
    
    elif "photographer" in prompt_lower or "photo" in prompt_lower or "picture" in prompt_lower or "shoot" in prompt_lower:
        if "rain" in condition:
            return f"Moody lighting at {temp}C! Perfect for dramatic shots. Puddle reflections create amazing images!"
        elif "sunny" in condition or "clear" in condition:
            return f"Golden hour coming at {temp}C in {city}! Perfect for outdoor shoots. HDR mode helpful!"
        elif "cloud" in condition or "overcast" in condition:
            return f"Overcast = natural softbox at {temp}C! Perfect for portraits and product photography. Ideal conditions!"
        else:
            return f"Good lighting conditions at {temp}C. Clear air gives sharp images!"
    
    # Default weather-based responses
    else:
        if "rain" in condition or "drizzle" in condition:
            return f"Rainy weather in {city} at {temp}C. Remember to carry an umbrella. Stay safe and enjoy the fresh smell!"
        elif "sunny" in condition or "clear" in condition:
            return f"Sunny weather in {city} at {temp}C. Great day to be outside! Sunscreen and hydration recommended."
        elif isinstance(temp, (int, float)) and temp > 30:
            return f"Hot weather in {city} at {temp}C! Stay hydrated and protect yourself from heat. Take cool breaks."
        elif isinstance(temp, (int, float)) and temp < 10:
            return f"Cold weather in {city} at {temp}C. Dress warmly and take care of yourself!"
        else:
            return f"Comfortable weather in {city} at {temp}C. Good conditions for outdoor activities!"

# Fallback for bye detection
def bye(text: str):
    """Check if text is a goodbye message"""
    try:
        # Try to use the @ai decorated version if available
        return bye_ai(text)
    except:
        # Fallback: simple keyword check
        bye_words = ["bye", "goodbye", "goodnight", "see you", "take care", "farewell", "later", "exit", "quit"]
        return "1" if any(word in text.lower() for word in bye_words) else "0"

# Try to create AI-powered bye detection
try:
    @ai
    def bye_ai(text: str):
        """Check if text is a bye message - return 1 or 0"""
        ...
except:
    pass

def isBye(text: str) -> bool:
    try:
        response: str = bye(text)
        output: bool = bool(int(response)) or False
        return output
    except:
        # Fallback to keyword check
        bye_words = ["bye", "goodbye", "goodnight", "see you", "take care", "farewell", "later", "exit", "quit"]
        return any(word in text.lower() for word in bye_words)
