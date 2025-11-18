# File: eco_friendly_lifestyle/ecofriendly.py

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, date
import random
import json
import asyncio
from pathlib import Path

DATA_FILE = Path("eco_data.json")  # simple persistence fallback
DATE_FMT = "%d-%m-%Y"

# Configurable points
POINTS = {
    "recycled": 10,
    "biked_or_walked": 15,
    "saved_energy": 8,
}

app = FastAPI(title="Eco-Friendly Lifestyle Bot 🌍", version="1.1")

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

# ---------- Pydantic models ----------
class User(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)

class UsersPayload(BaseModel):
    users: List[User]

class EcoChoice(BaseModel):
    username: str
    recycled: bool = False
    biked_or_walked: bool = False
    saved_energy: bool = False

class LogResponse(BaseModel):
    message: str
    username: str
    points_earned: int
    total_points: int
    date: str

class RegisterResponse(BaseModel):
    message: str
    usernames: List[str]

class LeaderItem(BaseModel):
    username: str
    points: int

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderItem]

class HistoryEntry(BaseModel):
    date: str
    recycled: bool
    biked_or_walked: bool
    saved_energy: bool
    points_earned: int

class UserHistoryResponse(BaseModel):
    username: str
    total_points: int
    history: List[HistoryEntry]

# ---------- In-memory structures (mirrors persistent store) ----------
# USER_POINTS: username -> int
# USER_HISTORY: username -> list of entries (each entry is a dict)
USER_POINTS: Dict[str, int] = {}
USER_HISTORY: Dict[str, List[Dict]] = {}

data_lock = asyncio.Lock()  # async-safe lock for file writes


# ---------- Persistence helpers ----------
def _load_data():
    if DATA_FILE.exists():
        try:
            blob = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            global USER_POINTS, USER_HISTORY
            USER_POINTS = blob.get("points", {})
            USER_HISTORY = blob.get("history", {})
        except Exception:
            # ignore and start fresh
            USER_POINTS.clear()
            USER_HISTORY.clear()

async def _save_data():
    payload = {"points": USER_POINTS, "history": USER_HISTORY}
    async with data_lock:
        # write to temp file then move for safer writes
        tmp = DATA_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(DATA_FILE)


# load on startup
_load_data()


# ---------- Helper utilities ----------
def today_str() -> str:
    return datetime.now().strftime(DATE_FMT)

def calculate_points(choice: EcoChoice) -> int:
    total = 0
    if choice.recycled:
        total += POINTS["recycled"]
    if choice.biked_or_walked:
        total += POINTS["biked_or_walked"]
    if choice.saved_energy:
        total += POINTS["saved_energy"]
    return total

def already_logged_today(username: str, day: str) -> bool:
    history = USER_HISTORY.get(username, [])
    return any(entry.get("date") == day for entry in history)

# ---------- Endpoints ----------

@app.post("/register/", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: User):
    """Register a single user. 201 if created, 200 with message if already exists."""
    if user.username in USER_POINTS:
        return {"message": "User already registered.", "usernames": [user.username]}
    USER_POINTS[user.username] = 0
    USER_HISTORY[user.username] = []
    await _save_data()
    return {"message": "User registered successfully.", "usernames": [user.username]}

@app.post("/register/batch/", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_users_batch(payload: UsersPayload):
    """Register multiple users in one request (accepts the JSON shape you tried earlier)."""
    created = []
    for u in payload.users:
        if u.username not in USER_POINTS:
            USER_POINTS[u.username] = 0
            USER_HISTORY[u.username] = []
            created.append(u.username)
    await _save_data()
    msg = "Users registered successfully." if created else "No new users created."
    return {"message": msg, "usernames": created or [u.username for u in payload.users]}

@app.post("/log-choice/", response_model=LogResponse)
async def log_choice(choice: EcoChoice):
    """Log daily choices. Prevents more than one log per day per user."""
    if choice.username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered.")

    day = today_str()
    if already_logged_today(choice.username, day):
        # Conflict - user already logged today
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Choices for {day} already logged for user {choice.username}."
        )

    points = calculate_points(choice)
    USER_POINTS[choice.username] += points

    entry = {
        "date": day,
        "recycled": choice.recycled,
        "biked_or_walked": choice.biked_or_walked,
        "saved_energy": choice.saved_energy,
        "points_earned": points,
    }
    USER_HISTORY.setdefault(choice.username, []).append(entry)
    await _save_data()

    return {
        "message": "Choices logged successfully!",
        "username": choice.username,
        "points_earned": points,
        "total_points": USER_POINTS[choice.username],
        "date": day
    }

@app.get("/eco-tip/{username}", status_code=status.HTTP_200_OK)
async def get_tip(username: str):
    if username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered.")
    tip = random.choice(ECO_TIPS)
    return {"username": username, "eco_tip": tip}

@app.get("/leaderboard/", response_model=LeaderboardResponse)
async def leaderboard(top: Optional[int] = 10):
    """Return top N users (default top 10)."""
    sorted_board = sorted(USER_POINTS.items(), key=lambda x: x[1], reverse=True)
    limited = sorted_board[:top]
    return {"leaderboard": [{"username": u, "points": p} for u, p in limited]}

@app.get("/history/{username}", response_model=UserHistoryResponse)
async def user_history(username: str):
    """Get user history of logged choices."""
    if username not in USER_POINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered.")
    history = USER_HISTORY.get(username, [])
    return {
        "username": username,
        "total_points": USER_POINTS.get(username, 0),
        "history": history
    }
