from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from lib.ai import analyze
import traceback
import sys


def _safe_print(*args, **kwargs):
    """Print safely to consoles that may not support Unicode (fallback to utf-8 bytes)."""
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            text = " ".join(str(a) for a in args) + ("\n" if not kwargs.get("end") else "")
            sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        except Exception:
            pass

app = Flask(__name__)
app.secret_key = "secret123"

# -------- WEATHER CODES --------
WEATHER_CODES = {
    0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Foggy", 51: "Light Drizzle", 53: "Moderate Drizzle",
    55: "Heavy Drizzle", 61: "Slight Rain", 63: "Moderate Rain",
    65: "Heavy Rain", 71: "Slight Snow", 73: "Moderate Snow",
    75: "Heavy Snow", 80: "Slight Rain Showers", 81: "Moderate Showers",
    82: "Heavy Showers", 85: "Slight Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Hail", 99: "Thunderstorm with Hail"
}

# -------- WEATHER FUNCTION --------
def get_real_weather(city):
    if not city:
        return None

    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_res = requests.get(geo_url).json()

        if not geo_res.get("results"):
            return None

        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=relativehumidity_2m,apparent_temperature,pressure_msl"
            f"&daily=weathercode,temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
        )
        data = requests.get(weather_url).json()

        current = data.get("current_weather")
        if not current:
            return None

        humidity = "N/A"
        feels = "N/A"
        pressure = "N/A"
        hourly = data.get("hourly", {})
        current_time = current.get("time")
        if current_time and hourly.get("time"):
            try:
                idx = hourly["time"].index(current_time)
                humidity = hourly.get("relativehumidity_2m", ["N/A"])[idx]
                pressure = hourly.get("pressure_msl", ["N/A"])[idx]
                feels = round(hourly.get("apparent_temperature", [current.get("temperature")])[idx])
            except ValueError:
                humidity = hourly.get("relativehumidity_2m", ["N/A"])[0]
                pressure = hourly.get("pressure_msl", ["N/A"])[0]
                feels = round(hourly.get("apparent_temperature", [current.get("temperature")])[0])

        forecast = []
        daily = data.get("daily", {})
        for i, day in enumerate(daily.get("time", [])):
            forecast.append({
                "date": day,
                "condition": WEATHER_CODES.get(daily.get("weathercode", [])[i], "Unknown"),
                "temp_max": round(daily.get("temperature_2m_max", [0])[i]),
                "temp_min": round(daily.get("temperature_2m_min", [0])[i])
            })

        return {
            "temp": round(current["temperature"]),
            "humidity": humidity,
            "pressure": pressure,
            "wind": current.get("windspeed", "N/A"),
            "feels": feels,
            "condition": WEATHER_CODES.get(current.get("weathercode"), "Unknown"),
            "city": city,
            "forecast": forecast
        }

    except:
        return None

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------- SIGNUP --------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = False

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if not user or not pwd or len(pwd) < 4:
            error = True
        else:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users VALUES (?, ?)", (user, pwd))
                conn.commit()
                conn.close()
                return redirect("/")
            except:
                error = True

    return render_template("signup.html", error=error)

# -------- LOGIN --------
@app.route("/", methods=["GET", "POST"])
def login():
    error = False

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (user,))
        result = c.fetchone()
        conn.close()

        if result and result[0] == pwd:
            session["user"] = user
            return redirect("/dashboard")
        else:
            error = True

    return render_template("login.html", error=error)

# -------- DASHBOARD --------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    # Update location and profile from form if provided
    form_location = request.form.get("location")
    form_profile = request.form.get("profile")

    if form_location:
        session["location"] = form_location

    if form_profile:
        session["profile"] = form_profile

    location = session.get("location", "Bangalore")
    profile = session.get("profile", "student")

    weather = get_real_weather(location)

    if not weather:
        weather = {
            "temp": "N/A",
            "humidity": "N/A",
            "pressure": "N/A",
            "wind": "N/A",
            "feels": "N/A",
            "condition": "Unknown",
            "city": location
        }

    return render_template(
        "dashboard.html",
        weather=weather,
        location=location,
        user=session["user"],
        profile=profile
    )

# -------- CHAT --------
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return redirect("/")

    msg = request.form.get("message")
    location = session.get("location", "Bangalore")

    weather = get_real_weather(location)

    # Build a minimal weather dict if unavailable so AI still has context
    if not weather:
        weather = {
            "temp": "N/A",
            "humidity": "N/A",
            "pressure": "N/A",
            "wind": "N/A",
            "feels": "N/A",
            "condition": "Unknown",
            "city": location,
            "forecast": []
        }

    # Include profile hint if present in session
    profile = session.get("profile")

    # Construct prompt similar to CLI flow: include user message and optional profile hints
    if profile:
        prompt = f"User asks: {msg} (Profile: {profile})"
    else:
        prompt = f"User asks: {msg}"

    try:
        _safe_print(f"[chat] message={msg!r} profile={profile!r} location={location!r}")
        response = analyze(weather, prompt)
        _safe_print("[chat] ai response:", response)
        return jsonify({"response": response, "user_input": msg})
    except Exception as e:
        tb = traceback.format_exc()
        print("[chat] analyze() raised exception:\n", tb)
        # Fallback simple weather reply on failure and include error for debugging
        response = f"In {location}, it is {weather.get('temp')}°C with {weather.get('condition')}."
        return jsonify({"response": response, "user_input": msg, "error": str(e)})

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)