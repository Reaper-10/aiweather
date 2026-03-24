from flask import Flask, render_template, request, redirect, session
import sqlite3
import asyncio
from lib import getweather, analyze, format
import requests

import requests

def get_real_weather(city):
    API_KEY = "PASTE_YOUR_REAL_KEY"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    res = requests.get(url).json()

    print("API RESPONSE:", res)

    if res.get("cod") != 200:
        return {
            "temp": "N/A",
            "humidity": "N/A",
            "pressure": "N/A",
            "wind": "N/A",
            "feels": "N/A",
            "uv": "N/A",
            "condition": "unknown"
        }

    return {
        "temp": res["main"]["temp"],
        "humidity": res["main"]["humidity"],
        "pressure": res["main"]["pressure"],
        "wind": res["wind"]["speed"],
        "feels": res["main"]["feels_like"],
        "uv": "N/A",
        "condition": res["weather"][0]["main"]
    }

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

weather_data = {}
user_profile = ""

# -------- PROFILE PROMPT --------
def build_prompt(raw, profile):
    return raw + f" (Give response for {profile} perspective)"

# -------- SIGNUP --------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users VALUES (?, ?)", (user, pwd))
            conn.commit()
        except:
            return "User already exists"

        return redirect("/")

    return render_template("signup.html")

# -------- LOGIN --------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        result = c.fetchone()

        if result:
            session["user"] = user
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html", error="1", weather={"condition": "sunny"})

# -------- DASHBOARD --------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    weather = {}

    if request.method == "POST":
        location = request.form.get("location") or "Bangalore"
        weather = get_real_weather(location)

    return render_template("dashboard.html",
                           user=session["user"],
                           weather=weather)

# -------- CHAT --------
@app.route("/chat", methods=["POST"])
def chat():
    msg = request.form["message"]

    prompt = build_prompt(msg, user_profile)
    response = format(analyze(weather_data, prompt))

    return render_template("dashboard.html",
                           user=session["user"],
                           response=response,
                           user_input=msg)

app.run(debug=True)