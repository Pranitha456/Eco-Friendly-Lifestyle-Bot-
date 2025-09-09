# File: main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List
import random
from datetime import datetime

app = FastAPI(title="Eco-Friendly Lifestyle Bot 🌍")

# In-memory user points
USER_POINTS: Dict[str, int] = {}

# Eco tips list
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

# ---------------- Models ----------------

# Single user
class User(BaseModel):
    username: str

class EcoChoice(BaseModel):
    username: str
    recycled: bool = False
    biked_or_walked: bool = False
    saved_energy: bool = False

# Multiple users
class MultipleUsers(BaseModel):
    users: List[User]

class MultipleEcoChoices(BaseModel):
    choices: List[EcoChoice]

class MultipleUsernames(BaseModel):
    usernames: List[str]

# ---------------- Single user endpoints ----------------

@app.post("/register/")
def register_user(user: User):
    """Register a single user"""
    if user.username in USER_POINTS:
        return {"message": "User already registered!", "username": user.username}
    USER_POINTS[user.username] = 0
    return {"message": "User registered successfully!", "username": user.username}

@app.post("/log-choice/")
def log_choice(choice: EcoChoice):
    """Log eco-friendly choices for a single user"""
    if choice.username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User '{choice.username}' not registered.")

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

# ---------------- Multiple users endpoints ----------------

@app.post("/register-multiple/")
def register_multiple_users(users_data: MultipleUsers):
    """Register multiple users"""
    registered = []
    already_registered = []

    for user in users_data.users:
        if user.username in USER_POINTS:
            already_registered.append(user.username)
        else:
            USER_POINTS[user.username] = 0
            registered.append(user.username)

    return {
        "registered": registered,
        "already_registered": already_registered
    }

@app.post("/log-choice-multiple/")
def log_choice_multiple(choices_data: MultipleEcoChoices):
    """Log choices for multiple users"""
    results = []

    for choice in choices_data.choices:
        if choice.username not in USER_POINTS:
            results.append({
                "username": choice.username,
                "error": "User not registered"
            })
            continue

        points = 0
        if choice.recycled:
            points += 10
        if choice.biked_or_walked:
            points += 15
        if choice.saved_energy:
            points += 8

        USER_POINTS[choice.username] += points

        results.append({
            "username": choice.username,
            "points_earned": points,
            "total_points": USER_POINTS[choice.username]
        })

    return {"results": results}

# ---------------- Eco tips ----------------

@app.get("/eco-tip/{username}")
def get_tip(username: str):
    """Get a random eco-tip for a single user"""
    if username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not registered.")
    tip = random.choice(ECO_TIPS)
    return {"username": username, "eco_tip": tip}

@app.post("/eco-tip-multiple/")
def get_tips_multiple(users_data: MultipleUsernames):
    """Get eco-tips for multiple users"""
    results = []

    for username in users_data.usernames:
        if username not in USER_POINTS:
            results.append({"username": username, "error": "User not registered"})
        else:
            tip = random.choice(ECO_TIPS)
            results.append({"username": username, "eco_tip": tip})

    return {"results": results}

# ---------------- Leaderboard ----------------

@app.get("/leaderboard/")
def leaderboard():
    """Get leaderboard of all users sorted by points"""
    sorted_board = sorted(USER_POINTS.items(), key=lambda x: x[1], reverse=True)
    return {
        "leaderboard": [{"username": u, "points": p} for u, p in sorted_board]
    }
