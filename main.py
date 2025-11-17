# File: eco_friendly_lifestyle/ecofriendly.py

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict
import random
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Eco-Friendly Lifestyle Bot 🌍")

# In-memory storage for user points
USER_POINTS: Dict[str, int] = {}

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

# Endpoint to register a user
@app.post("/register/")
def register_user(user: User):
    if user.username in USER_POINTS:
        return {"message": "User already registered!", "username": user.username}
    USER_POINTS[user.username] = 0
    return {"message": "User registered successfully!", "username": user.username}

# Endpoint to log daily eco choices
@app.post("/log-choice/")
def log_choice(choice: EcoChoice):
    if choice.username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered.")

    points = 0
    if choice.recycled:
        points += 10
    if choice.biked_or_walked:
        points += 15
    if choice.saved_energy:
        points += 8

    USER_POINTS[choice.username] += points

    return {
        "message": "Choices logged successfully!",
        "username": choice.username,
        "points_earned": points,
        "total_points": USER_POINTS[choice.username],
        "date": datetime.now().strftime("%d-%m-%Y")
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
