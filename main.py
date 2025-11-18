# File: eco_friendly_lifestyle/ecofriendly.py

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List
import random
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Eco-Friendly Lifestyle Bot 🌍")

# In-memory storage for user points and history
USER_POINTS: Dict[str, int] = {}
USER_HISTORY: Dict[str, List[Dict]] = {}

DATE_FMT = "%d-%m-%Y"

# List of eco-friendly tips
ECO_TIPS = [
    "Turn off lights when not in use 💡",
    "Use reusable bags instead of plastic 🛍️",
    "Compost your kitchen waste 🍃",
    "Unplug chargers when not charging 🔌",
    "Reduce shower time to save water 🚿",
    "Plant a tree or indoor plant 🌱",
    "Use public transport or carpool 🚍",
    "Switch to a refillable water bottle 💧"
]

# Pydantic models for request bodies
class User(BaseModel):
    username: str

class EcoChoice(BaseModel):
    username: str
    recycled: bool = False
    biked_or_walked: bool = False
    saved_energy: bool = False

# Helpers
def today_str() -> str:
    return datetime.now().strftime(DATE_FMT)

def already_logged_today(username: str, day: str) -> bool:
    history = USER_HISTORY.get(username, [])
    return any(entry.get("date") == day for entry in history)

def calculate_points_from_choice(choice: EcoChoice) -> int:
    points = 0
    if choice.recycled:
        points += 10
    if choice.biked_or_walked:
        points += 15
    if choice.saved_energy:
        points += 8
    return points

# Endpoint to register a user
@app.post("/register/", status_code=status.HTTP_201_CREATED)
def register_user(user: User):
    if user.username in USER_POINTS:
        return {"message": "User already registered!", "username": user.username}
    USER_POINTS[user.username] = 0
    USER_HISTORY[user.username] = []
    return {"message": "User registered successfully!", "username": user.username}

# Endpoint to log daily eco choices
@app.post("/log-choice/")
def log_choice(choice: EcoChoice):
    if choice.username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered.")

    day = today_str()
    if already_logged_today(choice.username, day):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Choices for {day} already logged for user {choice.username}."
        )

    points = calculate_points_from_choice(choice)
    USER_POINTS[choice.username] += points

    entry = {
        "date": day,
        "recycled": choice.recycled,
        "biked_or_walked": choice.biked_or_walked,
        "saved_energy": choice.saved_energy,
        "points_earned": points
    }
    USER_HISTORY.setdefault(choice.username, []).append(entry)

    return {
        "message": "Choices logged successfully!",
        "username": choice.username,
        "points_earned": points,
        "total_points": USER_POINTS[choice.username],
        "date": day
    }

# Endpoint to get a random eco tip
@app.get("/eco-tip/{username}")
def get_tip(username: str):
    if username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered.")
    tip = random.choice(ECO_TIPS)
    return {"username": username, "eco_tip": tip}

# Endpoint to get leaderboard
@app.get("/leaderboard/")
def leaderboard():
    sorted_board = sorted(USER_POINTS.items(), key=lambda x: x[1], reverse=True)
    return {"leaderboard": [{"username": u, "points": p} for u, p in sorted_board]}

# Endpoint to get user history (and total points)
@app.get("/history/{username}")
def user_history(username: str):
    if username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered.")
    history = USER_HISTORY.get(username, [])
    return {
        "username": username,
        "total_points": USER_POINTS.get(username, 0),
        "history": history
    }
