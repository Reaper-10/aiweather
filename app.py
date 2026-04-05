from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,pressure_msl"
        data = requests.get(weather_url).json()

        current = data["current"]

        return {
            "temp": round(current["temperature_2m"]),
            "humidity": current["relative_humidity_2m"],
            "pressure": current.get("pressure_msl", 1013),
            "wind": current["wind_speed_10m"],
            "feels": round(current["apparent_temperature"]),
            "condition": WEATHER_CODES.get(current["weather_code"], "Unknown"),
            "city": city
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

    location = request.form.get("location") or session.get("location", "Bangalore")
    session["location"] = location

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
        user=session["user"]
    )

# -------- CHAT --------
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return redirect("/")

    msg = request.form.get("message")
    location = session.get("location", "Bangalore")

    weather = get_real_weather(location)

    if weather:
        response = f"In {location}, it is {weather['temp']}°C with {weather['condition']}."
    else:
        response = "Weather data unavailable."

    return jsonify({"response": response})

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)