user_name = ""
user_profile = ""
from lib import *
import asyncio
import os
from typing import Dict

def main() -> None:
    global user_name, user_profile

    # -------- LOGIN --------
    display("Enter your name: ", end="")
    user_name = input()

    display("\nSelect your profile:\n")
    display("1. Farmer 🌾")
    display("2. Gym 💪")
    display("3. Student 📚")
    display("4. Traveler 🧳")
    display("5. Sports Player 🏏")
    display("6. Office Worker 🧑‍💼")
    display("7. Delivery Rider 🚴")
    display("8. Homemaker 🏡")
    display("9. Photographer 📸")
    display("Enter choice (1-9): ", end="")

    choice = input()

    profiles = {
        "1": "farmer",
        "2": "gym",
        "3": "student",
        "4": "traveler",
        "5": "sports",
        "6": "office",
        "7": "rider",
        "8": "home",
        "9": "photographer"
    }

    user_profile = profiles.get(choice, "student")

    display(f"\nWelcome {user_name}! Profile: {user_profile.upper()} 🚀\n")

    # -------- LOCATION --------
    display("Location : ", end="")
    location: str = input() 

    result: Dict = asyncio.run(getweather(location.capitalize()))
    clear()

    # -------- MAIN LOOP --------
    def mainloop() -> None:
        while True:
            display("You: ", end="")
            raw_prompt: str = input()

            # -------- PROFILE LOGIC --------
            if user_profile == "farmer":
                prompt = raw_prompt + " (Focus on crops, rainfall, soil moisture, irrigation advice)"

            elif user_profile == "gym":
                prompt = raw_prompt + " (Focus on workouts, hydration, outdoor fitness conditions)"

            elif user_profile == "student":
                prompt = raw_prompt + " (Focus on comfort, concentration, study environment)"

            elif user_profile == "traveler":
                prompt = raw_prompt + " (Focus on travel safety, packing suggestions, sightseeing conditions)"

            elif user_profile == "sports":
                prompt = raw_prompt + " (Focus on outdoor play conditions, stamina, weather impact on sports)"

            elif user_profile == "office":
                prompt = raw_prompt + " (Focus on commute, traffic impact, daily routine comfort)"

            elif user_profile == "rider":
                prompt = raw_prompt + " (Focus on road safety, rain impact, visibility, delivery conditions)"

            elif user_profile == "home":
                prompt = raw_prompt + " (Focus on daily home activities, laundry, cooking conditions)"

            elif user_profile == "photographer":
                prompt = raw_prompt + " (Focus on lighting, sky conditions, best time for photos)"

            else:
                prompt = raw_prompt

            is_bye: bool = isBye(raw_prompt)
            if is_bye or "bye" in raw_prompt.lower():
                display("AI: ", "Bye. Have a nice day.")
                break

            response: Final[str] = format(analyze(result, prompt))
            display("AI: ", response)

    mainloop()

if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

main()