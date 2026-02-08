from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import uuid
from datetime import datetime, timedelta
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'training_engine')]

# Admin password (default: admin123)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===========================
# PRESCRIPTION TYPES
# ===========================

PRESCRIPTION_TYPES = {
    "KB_STRENGTH": {
        "id": "KB_STRENGTH",
        "name": "Kettlebell Strength",
        "output_fields": ["sets", "reps", "rest"],
        "description": "Standard kettlebell strength work with ladders or sets across"
    },
    "BW_DYNAMIC": {
        "id": "BW_DYNAMIC",
        "name": "Bodyweight Dynamic",
        "output_fields": ["sets", "reps", "rest", "tempo"],
        "description": "Dynamic bodyweight movements with rep targets"
    },
    "ISOMETRIC_HOLD": {
        "id": "ISOMETRIC_HOLD",
        "name": "Isometric Hold",
        "output_fields": ["sets", "hold_time", "rest"],
        "description": "Static holds for time, no reps"
    },
    "CARRY_TIME": {
        "id": "CARRY_TIME",
        "name": "Carry (Time-based)",
        "output_fields": ["sets", "time", "rest", "load"],
        "description": "Loaded carries measured by time"
    },
    "CRAWL_TIME": {
        "id": "CRAWL_TIME",
        "name": "Crawl (Time-based)",
        "output_fields": ["sets", "time", "rest"],
        "description": "Crawling patterns measured by time"
    },
    "POWER_SWING": {
        "id": "POWER_SWING",
        "name": "Power (Swings)",
        "output_fields": ["sets", "reps", "rest"],
        "description": "Explosive power work, gated by recovery"
    }
}

# ===========================
# DEFAULT DATA (for seeding)
# ===========================

DEFAULT_PROTOCOLS = [
    # KB_STRENGTH Protocols
    {
        "id": "ladder_123",
        "name": "Ladder 1-2-3",
        "prescription_type": "KB_STRENGTH",
        "description_short": "Perform reps 1, then 2, then 3, rest 60-90s between rungs. That's one ladder. Do 3-5 ladders total.",
        "example": "Rung 1 → rest → Rung 2 → rest → Rung 3 → rest → repeat",
        "sets": "3-5 ladders",
        "reps": "1, 2, 3",
        "rest": "60-90s",
        "is_easy_day": False
    },
    {
        "id": "ladder_12345",
        "name": "Ladder 1-2-3-4-5",
        "prescription_type": "KB_STRENGTH",
        "description_short": "Perform reps 1, 2, 3, 4, 5 with rest 60-90s between rungs. Do 2-3 ladders total. High volume day.",
        "example": "1-2-3-4-5 = 15 reps per ladder",
        "sets": "2-3 ladders",
        "reps": "1, 2, 3, 4, 5",
        "rest": "60-90s",
        "is_easy_day": False
    },
    {
        "id": "sets_across_kb",
        "name": "Sets Across",
        "prescription_type": "KB_STRENGTH",
        "description_short": "Same reps each set. Focus on crisp, quality reps. Stop 1 rep before you grind.",
        "example": "5 sets of 5 reps, same weight",
        "sets": "3-5",
        "reps": "5",
        "rest": "60-90s",
        "is_easy_day": False
    },
    {
        "id": "density_block",
        "name": "Density Block",
        "prescription_type": "KB_STRENGTH",
        "description_short": "Accumulate crisp sets for a fixed time. Rest as needed. Stop before form breaks.",
        "example": "10 minutes, sets of 3-5, rest as needed",
        "sets": "AMRAP",
        "reps": "3-5",
        "rest": "10 min total",
        "is_easy_day": False
    },
    # BW_DYNAMIC Protocols
    {
        "id": "sets_across_bw",
        "name": "Sets Across",
        "prescription_type": "BW_DYNAMIC",
        "description_short": "Same reps each set. Quality over quantity. Full range of motion.",
        "example": "4 sets of 8 reps",
        "sets": "3-5",
        "reps": "5-8",
        "rest": "60-90s",
        "is_easy_day": False
    },
    {
        "id": "total_reps_target",
        "name": "Total Reps Target",
        "prescription_type": "BW_DYNAMIC",
        "description_short": "Accumulate the target number of quality reps in as many sets as needed. Rest as needed.",
        "example": "Get 50 total push-ups, however you want",
        "sets": "As needed",
        "reps": "Total 30-50",
        "rest": "As needed",
        "is_easy_day": False
    },
    {
        "id": "tempo_sets",
        "name": "Tempo Sets",
        "prescription_type": "BW_DYNAMIC",
        "description_short": "Control the tempo: 3 seconds down, 1 second pause, up crisp. Builds strength and control.",
        "example": "3-1-1 tempo: 3s down, 1s pause, 1s up",
        "sets": "3-5",
        "reps": "5-8",
        "rest": "60-90s",
        "tempo": "3-1-1",
        "is_easy_day": False
    },
    # ISOMETRIC_HOLD Protocols
    {
        "id": "hardstyle_hold",
        "name": "Hardstyle Hold",
        "prescription_type": "ISOMETRIC_HOLD",
        "description_short": "Maximum tension for short duration. Squeeze everything: glutes, abs, lats. Quality over duration.",
        "example": "7-15 seconds of maximum effort",
        "sets": "4-6",
        "hold_time": "7-15s",
        "rest": "45-75s",
        "is_easy_day": False
    },
    {
        "id": "submax_hold",
        "name": "Submax Hold",
        "prescription_type": "ISOMETRIC_HOLD",
        "description_short": "Moderate tension, longer duration. Focus on maintaining perfect position.",
        "example": "15-30 seconds at 70% effort",
        "sets": "3-5",
        "hold_time": "15-30s",
        "rest": "60s",
        "is_easy_day": False
    },
    # CARRY_TIME Protocols
    {
        "id": "carry_time_standard",
        "name": "Timed Carry",
        "prescription_type": "CARRY_TIME",
        "description_short": "Carry for time, not distance. Walk slow and controlled. Maintain tall posture throughout.",
        "example": "Walk for 30-60 seconds per set",
        "sets": "3-6",
        "time": "30-60s",
        "rest": "60-90s",
        "is_easy_day": False
    },
    {
        "id": "carry_time_heavy",
        "name": "Heavy Carry",
        "prescription_type": "CARRY_TIME",
        "description_short": "Heavier load, shorter duration. More sets. Challenge your grip and core.",
        "example": "Heavy for 20-30 seconds, more sets",
        "sets": "5-8",
        "time": "20-30s",
        "rest": "60-90s",
        "is_easy_day": False
    },
    # CRAWL_TIME Protocols
    {
        "id": "crawl_time_standard",
        "name": "Timed Crawl",
        "prescription_type": "CRAWL_TIME",
        "description_short": "Crawl for time, not distance. Stay low, move smooth. Opposite hand and foot together.",
        "example": "Crawl for 20-40 seconds per set",
        "sets": "3-6",
        "time": "20-40s",
        "rest": "40-60s",
        "is_easy_day": False
    },
    # POWER_SWING Protocols
    {
        "id": "swing_emom",
        "name": "EMOM Swings",
        "prescription_type": "POWER_SWING",
        "description_short": "Every Minute on the Minute. Do your swings, rest the remainder. Crisp and explosive every rep.",
        "example": "10 swings at top of each minute for 10 mins",
        "sets": "10-15 min",
        "reps": "10",
        "rest": "Remainder of minute",
        "is_easy_day": False
    },
    {
        "id": "swing_sets_across",
        "name": "Swing Sets",
        "prescription_type": "POWER_SWING",
        "description_short": "Traditional sets with fixed rest. Every rep should be explosive. Stop if power drops.",
        "example": "6-10 sets of 10-15 reps",
        "sets": "6-10",
        "reps": "10-15",
        "rest": "45-75s",
        "is_easy_day": False
    },
    # EASY day protocols
    {
        "id": "light_practice_kb",
        "name": "Light Practice",
        "prescription_type": "KB_STRENGTH",
        "description_short": "Light weight, low volume. Focus on perfect technique. This is a recovery session.",
        "example": "Light bell, crisp reps, plenty of rest",
        "sets": "2-3",
        "reps": "3-5",
        "rest": "90s+",
        "is_easy_day": True
    },
    {
        "id": "light_practice_bw",
        "name": "Light Practice",
        "prescription_type": "BW_DYNAMIC",
        "description_short": "Easy bodyweight work. Focus on movement quality. This is a recovery session.",
        "example": "Slow, controlled reps",
        "sets": "2-3",
        "reps": "5-8",
        "rest": "As needed",
        "is_easy_day": True
    },
    {
        "id": "light_hold",
        "name": "Light Hold",
        "prescription_type": "ISOMETRIC_HOLD",
        "description_short": "Easy holds. Moderate tension. Recovery work.",
        "example": "Comfortable holds, breathing controlled",
        "sets": "2-3",
        "hold_time": "10-20s",
        "rest": "60s",
        "is_easy_day": True
    },
    {
        "id": "light_carry",
        "name": "Light Carry",
        "prescription_type": "CARRY_TIME",
        "description_short": "Easy carries. Light weight, shorter duration. Recovery work.",
        "example": "Light load, relaxed walk",
        "sets": "2-3",
        "time": "20-30s",
        "rest": "60s",
        "is_easy_day": True
    },
    {
        "id": "light_crawl",
        "name": "Light Crawl",
        "prescription_type": "CRAWL_TIME",
        "description_short": "Easy crawling. Focus on smooth movement. Recovery work.",
        "example": "Slow and controlled",
        "sets": "2-3",
        "time": "15-20s",
        "rest": "45s",
        "is_easy_day": True
    }
]

DEFAULT_EXERCISES = [
    # SQUAT category
    {"id": "kb_goblet_squat", "name": "KB Goblet Squat", "category": "squat", "equipment": ["home", "minimal"], "bilateral": True, "is_anchor": False, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "single_kb_front_squat", "name": "Single KB Front Squat", "category": "squat", "equipment": ["home", "minimal"], "bilateral": True, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "double_kb_front_squat", "name": "Double KB Front Squat", "category": "squat", "equipment": ["home"], "bilateral": True, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "kb_split_squat", "name": "KB Split Squat", "category": "squat", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "kb_rfess", "name": "KB Rear Foot Elevated Split Squat", "category": "squat", "equipment": ["home"], "bilateral": False, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "atg_split_squat", "name": "ATG Split Squat", "category": "squat", "equipment": ["home", "minimal", "bodyweight"], "bilateral": False, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "rear_leg_assisted_shrimp", "name": "Rear Leg Assisted Shrimp", "category": "squat", "equipment": ["home", "minimal", "bodyweight"], "bilateral": False, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "kb_lunge", "name": "KB Lunge", "category": "squat", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "bw_lunge", "name": "Bodyweight Lunge", "category": "squat", "equipment": ["home", "minimal", "bodyweight"], "bilateral": False, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    # HINGE category
    {"id": "kb_sumo_deadlift", "name": "KB Sumo Deadlift", "category": "hinge", "equipment": ["home", "minimal"], "bilateral": True, "is_anchor": False, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "kb_suitcase_deadlift", "name": "KB Suitcase Deadlift", "category": "hinge", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "single_leg_kb_deadlift", "name": "Single Leg KB Deadlift", "category": "hinge", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "hip_thrust", "name": "Hip Thrust", "category": "hinge", "equipment": ["home"], "bilateral": True, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "single_leg_hip_thrust", "name": "Single Leg Hip Thrust", "category": "hinge", "equipment": ["home", "minimal", "bodyweight"], "bilateral": False, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "band_hip_thrust", "name": "Band Hip Thrust", "category": "hinge", "equipment": ["home"], "bilateral": True, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "kb_swing", "name": "KB Swing", "category": "hinge", "equipment": ["home", "minimal"], "bilateral": True, "is_anchor": False, "prescription_type": "POWER_SWING", "is_power": True},
    # PUSH category
    {"id": "pushup", "name": "Push-up", "category": "push", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": True, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "kb_press_single", "name": "KB Military Press (Single)", "category": "push", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "kb_press_double", "name": "KB Military Press (Double)", "category": "push", "equipment": ["home"], "bilateral": True, "is_anchor": True, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "floor_press_single", "name": "Floor Press (Single)", "category": "push", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "floor_press_double", "name": "Floor Press (Double)", "category": "push", "equipment": ["home"], "bilateral": True, "is_anchor": False, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "diamond_pushup", "name": "Diamond Push-up", "category": "push", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "deficit_pushup", "name": "Deficit Push-up", "category": "push", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "sfg_plank", "name": "SFG Plank", "category": "push", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": False, "prescription_type": "ISOMETRIC_HOLD", "is_power": False},
    {"id": "pushup_plank", "name": "Push-up Plank", "category": "push", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": False, "prescription_type": "ISOMETRIC_HOLD", "is_power": False},
    # PULL category
    {"id": "pullup", "name": "Pull-up", "category": "pull", "equipment": ["home"], "bilateral": True, "is_anchor": True, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "chinup", "name": "Chin-up", "category": "pull", "equipment": ["home"], "bilateral": True, "is_anchor": True, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "australian_pullup", "name": "Australian Pull-up", "category": "pull", "equipment": ["home"], "bilateral": True, "is_anchor": False, "prescription_type": "BW_DYNAMIC", "is_power": False},
    {"id": "kb_row", "name": "KB Row", "category": "pull", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "KB_STRENGTH", "is_power": False},
    {"id": "bw_batwing_hold", "name": "Bodyweight Batwing Hold", "category": "pull", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": False, "prescription_type": "ISOMETRIC_HOLD", "is_power": False},
    # CARRY category
    {"id": "farmer_carry", "name": "Farmer Carry", "category": "carry", "equipment": ["home", "minimal"], "bilateral": True, "is_anchor": True, "prescription_type": "CARRY_TIME", "is_power": False},
    {"id": "suitcase_carry", "name": "Suitcase Carry", "category": "carry", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "CARRY_TIME", "is_power": False},
    {"id": "rack_carry", "name": "Rack Carry", "category": "carry", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "CARRY_TIME", "is_power": False},
    {"id": "overhead_carry", "name": "Overhead Carry", "category": "carry", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "CARRY_TIME", "is_power": False},
    {"id": "bottom_up_carry", "name": "Bottom Up Carry", "category": "carry", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "CARRY_TIME", "is_power": False},
    {"id": "stationary_march_goblet", "name": "Stationary March (Goblet)", "category": "carry", "equipment": ["home", "minimal"], "bilateral": True, "is_anchor": False, "prescription_type": "CARRY_TIME", "is_power": False},
    {"id": "stationary_march_rack", "name": "Stationary March (Rack)", "category": "carry", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "CARRY_TIME", "is_power": False},
    {"id": "stationary_march_overhead", "name": "Stationary March (Overhead)", "category": "carry", "equipment": ["home", "minimal"], "bilateral": False, "is_anchor": False, "prescription_type": "CARRY_TIME", "is_power": False},
    # CRAWL category
    {"id": "bear_crawl", "name": "Bear Crawl", "category": "crawl", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": False, "prescription_type": "CRAWL_TIME", "is_power": False},
    {"id": "tiger_crawl", "name": "Tiger Crawl", "category": "crawl", "equipment": ["home", "minimal", "bodyweight"], "bilateral": True, "is_anchor": False, "prescription_type": "CRAWL_TIME", "is_power": False},
]

# Priority bucket rotation order
BUCKET_ROTATION = ["squat", "pull", "hinge", "push"]

# ===========================
# PYDANTIC MODELS
# ===========================

class QuestionnaireInput(BaseModel):
    feeling: Literal["bad", "ok", "great"]
    sleep: Literal["bad", "good"]
    pain: Literal["none", "present"]
    time_available: Literal["20-30", "30-45", "45-60"]
    equipment: Literal["home", "minimal", "bodyweight"]
    override_bucket: Optional[str] = None

class ExerciseOutput(BaseModel):
    id: str
    name: str
    category: str
    prescription_type: str
    load_level: str
    protocol_id: str
    protocol_name: str
    protocol_description: str
    sets: str
    reps: Optional[str] = None
    hold_time: Optional[str] = None
    time: Optional[str] = None
    rest: str
    tempo: Optional[str] = None
    notes: str = ""

class SessionOutput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    day_type: Literal["easy", "medium", "hard"]
    priority_bucket: str
    exercises: List[ExerciseOutput]
    time_slot: str
    equipment: str
    week_mode: str

class UserState(BaseModel):
    id: str = "user_state"
    next_priority_bucket: str = "squat"
    week_mode: Literal["A", "B"] = "A"
    week_mode_last_changed: datetime = Field(default_factory=datetime.utcnow)
    cooldown_counter: int = 0
    cooldown_override: bool = False
    power_last_used: Optional[datetime] = None
    last_hard_day: bool = False
    last_session_exercises: List[str] = []
    power_frequency: Literal["weekly", "fortnightly"] = "fortnightly"

class Benchmarks(BaseModel):
    id: str = "benchmarks"
    press_bell_kg: Optional[int] = None
    press_reps: Optional[int] = None
    pushup_max: Optional[int] = None
    pullup_max: Optional[int] = None
    front_squat_bells_kg: Optional[List[int]] = None
    front_squat_reps: Optional[int] = None
    hinge_bell_kg: Optional[int] = None
    hinge_reps: Optional[int] = None
    available_bells_minimal: List[int] = [16, 24, 28, 32]

class BenchmarksUpdate(BaseModel):
    press_bell_kg: Optional[int] = None
    press_reps: Optional[int] = None
    pushup_max: Optional[int] = None
    pullup_max: Optional[int] = None
    front_squat_bells_kg: Optional[List[int]] = None
    front_squat_reps: Optional[int] = None
    hinge_bell_kg: Optional[int] = None
    hinge_reps: Optional[int] = None
    available_bells_minimal: Optional[List[int]] = None

class SettingsUpdate(BaseModel):
    week_mode: Optional[Literal["A", "B"]] = None
    power_frequency: Optional[Literal["weekly", "fortnightly"]] = None
    cooldown_override: Optional[bool] = None

class SessionFeedback(BaseModel):
    session_id: str
    feedback: Literal["good", "not_good"]

class SwapRequest(BaseModel):
    session_id: str
    exercise_id: str
    equipment: str

class RerollRequest(BaseModel):
    questionnaire: QuestionnaireInput
    preserve_day_type: str
    preserve_priority_bucket: str

# Admin models
class AdminLogin(BaseModel):
    password: str

class ExerciseCreate(BaseModel):
    id: str
    name: str
    category: str
    equipment: List[str]
    bilateral: bool = True
    is_anchor: bool = False
    prescription_type: str
    is_power: bool = False
    custom_protocols: Optional[List[str]] = None  # Protocol IDs specific to this exercise

class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    equipment: Optional[List[str]] = None
    bilateral: Optional[bool] = None
    is_anchor: Optional[bool] = None
    prescription_type: Optional[str] = None
    is_power: Optional[bool] = None
    custom_protocols: Optional[List[str]] = None

class ProtocolCreate(BaseModel):
    id: str
    name: str
    prescription_type: str
    description_short: str
    example: Optional[str] = None
    sets: str
    reps: Optional[str] = None
    hold_time: Optional[str] = None
    time: Optional[str] = None
    rest: str
    tempo: Optional[str] = None
    is_easy_day: bool = False

class ProtocolUpdate(BaseModel):
    name: Optional[str] = None
    prescription_type: Optional[str] = None
    description_short: Optional[str] = None
    example: Optional[str] = None
    sets: Optional[str] = None
    reps: Optional[str] = None
    hold_time: Optional[str] = None
    time: Optional[str] = None
    rest: Optional[str] = None
    tempo: Optional[str] = None
    is_easy_day: Optional[bool] = None

# ===========================
# AUTH HELPER
# ===========================

def verify_admin(password: str) -> bool:
    return password == ADMIN_PASSWORD

def get_admin_token(password: str) -> str:
    """Generate a simple token for admin session"""
    return hashlib.sha256(f"{password}:{ADMIN_PASSWORD}".encode()).hexdigest()

def verify_admin_token(token: str) -> bool:
    """Verify admin token"""
    expected = hashlib.sha256(f"{ADMIN_PASSWORD}:{ADMIN_PASSWORD}".encode()).hexdigest()
    return token == expected

# ===========================
# DATABASE HELPERS
# ===========================

async def seed_database():
    """Seed database with default exercises and protocols if empty"""
    # Check if exercises exist
    exercise_count = await db.exercises.count_documents({})
    if exercise_count == 0:
        logger.info("Seeding exercises...")
        await db.exercises.insert_many(DEFAULT_EXERCISES)
        logger.info(f"Seeded {len(DEFAULT_EXERCISES)} exercises")
    
    # Check if protocols exist
    protocol_count = await db.protocols.count_documents({})
    if protocol_count == 0:
        logger.info("Seeding protocols...")
        await db.protocols.insert_many(DEFAULT_PROTOCOLS)
        logger.info(f"Seeded {len(DEFAULT_PROTOCOLS)} protocols")

async def get_exercise_library() -> Dict[str, dict]:
    """Get all exercises from database"""
    exercises = await db.exercises.find({}, {"_id": 0}).to_list(1000)
    return {ex["id"]: ex for ex in exercises}

async def get_protocol_library() -> Dict[str, dict]:
    """Get all protocols from database"""
    protocols = await db.protocols.find({}, {"_id": 0}).to_list(1000)
    return {proto["id"]: proto for proto in protocols}

async def get_user_state() -> UserState:
    """Get or create user state"""
    state = await db.user_state.find_one({"id": "user_state"}, {"_id": 0})
    if state:
        return UserState(**state)
    new_state = UserState()
    await db.user_state.insert_one(new_state.dict())
    return new_state

async def update_user_state(updates: dict):
    """Update user state"""
    await db.user_state.update_one(
        {"id": "user_state"},
        {"$set": updates},
        upsert=True
    )

async def get_benchmarks() -> Benchmarks:
    """Get or create benchmarks"""
    bench = await db.benchmarks.find_one({"id": "benchmarks"}, {"_id": 0})
    if bench:
        return Benchmarks(**bench)
    new_bench = Benchmarks()
    await db.benchmarks.insert_one(new_bench.dict())
    return new_bench

# ===========================
# SESSION GENERATION HELPERS
# ===========================

async def get_exercises_for_bucket(bucket: str, equipment: str, week_mode: str, exclude_ids: List[str] = []) -> List[dict]:
    """Get available exercises for a bucket filtered by equipment and week mode"""
    exercise_library = await get_exercise_library()
    exercises = []
    for ex_id, ex in exercise_library.items():
        if ex["category"] != bucket:
            continue
        if equipment not in ex["equipment"]:
            continue
        if ex_id in exclude_ids:
            continue
        exercises.append(ex)
    return exercises

def determine_day_type(questionnaire: QuestionnaireInput, state: UserState) -> str:
    """Determine day type based on questionnaire and state"""
    if questionnaire.pain == "present":
        return "easy"
    if questionnaire.feeling == "bad":
        return "easy"
    if questionnaire.sleep == "bad":
        return "easy"
    
    if state.cooldown_counter > 0 and not state.cooldown_override:
        return "easy"
    
    if state.last_hard_day:
        return "easy"
    
    if questionnaire.feeling == "great" and questionnaire.sleep == "good" and questionnaire.pain == "none":
        return random.choice(["medium", "hard"])
    
    return "medium"

def can_use_power(state: UserState, day_type: str, questionnaire: QuestionnaireInput) -> bool:
    """Check if power exercises (swings) can be used"""
    if day_type != "hard":
        return False
    if questionnaire.pain != "none":
        return False
    if questionnaire.sleep != "good":
        return False
    if questionnaire.feeling != "great":
        return False
    if state.cooldown_counter > 0:
        return False
    
    if state.power_last_used:
        days_since_power = (datetime.utcnow() - state.power_last_used).days
        if state.power_frequency == "weekly" and days_since_power < 7:
            return False
        if state.power_frequency == "fortnightly" and days_since_power < 14:
            return False
    
    return True

async def select_exercise_from_bucket(bucket: str, equipment: str, week_mode: str, exclude_ids: List[str], prefer_anchor: bool = True) -> Optional[dict]:
    """Select a single exercise from a bucket"""
    exercises = await get_exercises_for_bucket(bucket, equipment, week_mode, exclude_ids)
    
    if not exercises:
        exercise_library = await get_exercise_library()
        for ex_id, ex in exercise_library.items():
            if ex["category"] == bucket and equipment in ex["equipment"] and ex_id not in exclude_ids:
                exercises.append(ex)
    
    if not exercises:
        return None
    
    if prefer_anchor:
        anchors = [ex for ex in exercises if ex.get("is_anchor", False)]
        if anchors:
            exercises = anchors
    
    if week_mode == "A":
        bilateral = [ex for ex in exercises if ex.get("bilateral", True)]
        if bilateral:
            exercises = bilateral
    elif week_mode == "B" and bucket in ["squat", "hinge"]:
        unilateral = [ex for ex in exercises if not ex.get("bilateral", True)]
        if unilateral:
            exercises = unilateral
    
    return random.choice(exercises) if exercises else None

async def get_protocols_for_exercise(ex: dict, day_type: str) -> List[dict]:
    """Get protocols for an exercise - checks custom_protocols first, then falls back to prescription_type"""
    protocol_library = await get_protocol_library()
    protocols = []
    
    # Check if exercise has custom protocols assigned
    custom_protocol_ids = ex.get("custom_protocols", [])
    if custom_protocol_ids:
        for proto_id in custom_protocol_ids:
            if proto_id in protocol_library:
                proto = protocol_library[proto_id]
                # Filter by day type
                if day_type == "easy" and proto.get("is_easy_day", False):
                    protocols.append(proto)
                elif day_type != "easy" and not proto.get("is_easy_day", False):
                    protocols.append(proto)
    
    # Fallback to prescription type matching
    if not protocols:
        prescription_type = ex.get("prescription_type", "KB_STRENGTH")
        for proto_id, proto in protocol_library.items():
            if proto["prescription_type"] == prescription_type:
                if day_type == "easy" and proto.get("is_easy_day", False):
                    protocols.append(proto)
                elif day_type != "easy" and not proto.get("is_easy_day", False):
                    protocols.append(proto)
    
    # Ultimate fallback
    if not protocols:
        prescription_type = ex.get("prescription_type", "KB_STRENGTH")
        for proto_id, proto in protocol_library.items():
            if proto["prescription_type"] == prescription_type:
                protocols.append(proto)
    
    return protocols

async def get_protocol_for_exercise(ex: dict, day_type: str) -> dict:
    """Get appropriate protocol for an exercise"""
    protocols = await get_protocols_for_exercise(ex, day_type)
    
    if not protocols:
        protocol_library = await get_protocol_library()
        return protocol_library.get("sets_across_kb", DEFAULT_PROTOCOLS[2])
    
    return random.choice(protocols)

async def get_load_level(ex: dict, day_type: str, benchmarks: Benchmarks, equipment: str) -> str:
    """Determine load level for an exercise"""
    prescription_type = ex.get("prescription_type", "KB_STRENGTH")
    
    if prescription_type in ["BW_DYNAMIC", "ISOMETRIC_HOLD", "CRAWL_TIME"]:
        if day_type == "easy":
            return "Light effort"
        elif day_type == "medium":
            return "Moderate effort"
        else:
            return "Max effort"
    
    if equipment == "bodyweight":
        return "Bodyweight"
    
    if day_type == "easy":
        return "Light (60-70%)"
    elif day_type == "medium":
        return "Moderate (75-85%)"
    else:
        return "Heavy (85-95%)"

def build_exercise_output(ex: dict, protocol: dict, load: str, notes: str = "") -> ExerciseOutput:
    """Build ExerciseOutput with correct fields based on prescription type"""
    prescription_type = ex.get("prescription_type", "KB_STRENGTH")
    
    output = ExerciseOutput(
        id=ex["id"],
        name=ex["name"],
        category=ex["category"],
        prescription_type=prescription_type,
        load_level=load,
        protocol_id=protocol["id"],
        protocol_name=protocol["name"],
        protocol_description=protocol["description_short"],
        sets=protocol.get("sets", "3-5"),
        rest=protocol.get("rest", "60s"),
        notes=notes
    )
    
    if prescription_type in ["KB_STRENGTH", "BW_DYNAMIC", "POWER_SWING"]:
        output.reps = protocol.get("reps", "5")
    elif prescription_type == "ISOMETRIC_HOLD":
        output.hold_time = protocol.get("hold_time", "10-20s")
    elif prescription_type in ["CARRY_TIME", "CRAWL_TIME"]:
        output.time = protocol.get("time", "30-60s")
    
    if "tempo" in protocol:
        output.tempo = protocol["tempo"]
    
    return output

async def generate_session(questionnaire: QuestionnaireInput, state: UserState, benchmarks: Benchmarks, is_reroll: bool = False, forced_day_type: str = None, forced_priority_bucket: str = None) -> SessionOutput:
    """Generate a training session"""
    if forced_day_type:
        day_type = forced_day_type
    else:
        day_type = determine_day_type(questionnaire, state)
    
    equipment = questionnaire.equipment
    week_mode = state.week_mode
    
    if forced_priority_bucket:
        priority_bucket = forced_priority_bucket
    elif questionnaire.override_bucket:
        priority_bucket = questionnaire.override_bucket
    else:
        priority_bucket = state.next_priority_bucket
    
    time_slot = questionnaire.time_available
    if time_slot == "20-30":
        max_exercises = 4
        include_carry = True
        include_crawl = False
        secondary_buckets = 1
    elif time_slot == "30-45":
        max_exercises = 5
        include_carry = True
        include_crawl = False
        secondary_buckets = 2
    else:
        max_exercises = 5
        include_carry = True
        include_crawl = True
        secondary_buckets = 3
    
    exercises = []
    used_ids = state.last_session_exercises[:1] if not is_reroll else []
    
    # 1. Priority bucket exercise
    primary_ex = await select_exercise_from_bucket(priority_bucket, equipment, week_mode, used_ids, prefer_anchor=True)
    if primary_ex:
        protocol = await get_protocol_for_exercise(primary_ex, day_type)
        load = await get_load_level(primary_ex, day_type, benchmarks, equipment)
        exercises.append(build_exercise_output(
            primary_ex, protocol, load, 
            notes="Priority" if primary_ex.get("is_anchor") else ""
        ))
        used_ids.append(primary_ex["id"])
    
    # 2. Secondary buckets
    other_buckets = [b for b in BUCKET_ROTATION if b != priority_bucket]
    random.shuffle(other_buckets)
    
    for i, bucket in enumerate(other_buckets[:secondary_buckets]):
        ex = await select_exercise_from_bucket(bucket, equipment, week_mode, used_ids, prefer_anchor=True)
        if ex:
            if ex.get("is_power") and not can_use_power(state, day_type, questionnaire):
                ex = await select_exercise_from_bucket(bucket, equipment, week_mode, used_ids + ["kb_swing"], prefer_anchor=True)
                if not ex:
                    continue
            
            protocol = await get_protocol_for_exercise(ex, day_type)
            load = await get_load_level(ex, day_type, benchmarks, equipment)
            exercises.append(build_exercise_output(ex, protocol, load))
            used_ids.append(ex["id"])
    
    # 3. Carry
    if include_carry and len(exercises) < max_exercises:
        carry_ex = await select_exercise_from_bucket("carry", equipment, week_mode, used_ids)
        if carry_ex:
            protocol = await get_protocol_for_exercise(carry_ex, day_type)
            load = await get_load_level(carry_ex, day_type, benchmarks, equipment)
            exercises.append(build_exercise_output(carry_ex, protocol, load, notes="Finisher"))
            used_ids.append(carry_ex["id"])
    
    # 4. Crawl
    if include_crawl and len(exercises) < max_exercises:
        crawl_ex = await select_exercise_from_bucket("crawl", equipment, week_mode, used_ids)
        if crawl_ex:
            protocol = await get_protocol_for_exercise(crawl_ex, day_type)
            exercises.append(build_exercise_output(crawl_ex, protocol, "Bodyweight", notes="Support"))
    
    return SessionOutput(
        day_type=day_type,
        priority_bucket=priority_bucket,
        exercises=exercises,
        time_slot=time_slot,
        equipment=equipment,
        week_mode=week_mode
    )

# ===========================
# API ROUTES
# ===========================

@api_router.get("/")
async def root():
    return {"message": "Daily Training Decision Engine API"}

@api_router.get("/exercises")
async def get_exercises():
    """Get all exercises in the library"""
    exercises = await db.exercises.find({}, {"_id": 0}).to_list(1000)
    return exercises

@api_router.get("/exercises/{category}")
async def get_exercises_by_category(category: str):
    """Get exercises by category"""
    exercises = await db.exercises.find({"category": category}, {"_id": 0}).to_list(100)
    return exercises

@api_router.get("/protocols")
async def get_protocols():
    """Get all protocol definitions"""
    protocols = await db.protocols.find({}, {"_id": 0}).to_list(100)
    return protocols

@api_router.get("/protocols/{protocol_id}")
async def get_protocol(protocol_id: str):
    """Get a specific protocol by ID"""
    protocol = await db.protocols.find_one({"id": protocol_id})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol

@api_router.get("/prescription-types")
async def get_prescription_types():
    """Get all prescription types"""
    return list(PRESCRIPTION_TYPES.values())

@api_router.get("/state")
async def get_state():
    """Get current user state"""
    state = await get_user_state()
    return state

@api_router.get("/benchmarks")
async def get_benchmarks_route():
    """Get user benchmarks"""
    return await get_benchmarks()

@api_router.put("/benchmarks")
async def update_benchmarks_route(updates: BenchmarksUpdate):
    """Update user benchmarks"""
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    if update_dict:
        await db.benchmarks.update_one(
            {"id": "benchmarks"},
            {"$set": update_dict},
            upsert=True
        )
    return await get_benchmarks()

@api_router.put("/settings")
async def update_settings(updates: SettingsUpdate):
    """Update user settings"""
    state = await get_user_state()
    update_dict = {}
    
    if updates.week_mode is not None:
        update_dict["week_mode"] = updates.week_mode
        update_dict["week_mode_last_changed"] = datetime.utcnow()
    
    if updates.power_frequency is not None:
        update_dict["power_frequency"] = updates.power_frequency
    
    if updates.cooldown_override is not None:
        update_dict["cooldown_override"] = updates.cooldown_override
    
    if update_dict:
        await update_user_state(update_dict)
    
    return await get_user_state()

@api_router.post("/generate", response_model=SessionOutput)
async def generate_session_route(questionnaire: QuestionnaireInput):
    """Generate a training session based on questionnaire"""
    state = await get_user_state()
    benchmarks = await get_benchmarks()
    
    current_week = datetime.utcnow().isocalendar()[1]
    expected_mode = "A" if current_week % 2 == 1 else "B"
    if state.week_mode != expected_mode:
        await update_user_state({
            "week_mode": expected_mode,
            "week_mode_last_changed": datetime.utcnow()
        })
        state = await get_user_state()
    
    session = await generate_session(questionnaire, state, benchmarks)
    
    await db.sessions.insert_one(session.dict())
    
    if questionnaire.pain == "present" or questionnaire.feeling == "bad" or questionnaire.sleep == "bad":
        await update_user_state({
            "cooldown_counter": 2,
            "cooldown_override": False
        })
    
    return session

@api_router.post("/reroll", response_model=SessionOutput)
async def reroll_session(request: RerollRequest):
    """Reroll the session"""
    state = await get_user_state()
    benchmarks = await get_benchmarks()
    
    session = await generate_session(
        request.questionnaire, 
        state, 
        benchmarks, 
        is_reroll=True,
        forced_day_type=request.preserve_day_type,
        forced_priority_bucket=request.preserve_priority_bucket
    )
    
    await db.sessions.delete_one({"id": session.id})
    await db.sessions.insert_one(session.dict())
    
    return session

@api_router.post("/swap")
async def swap_exercise(request: SwapRequest):
    """Swap a single exercise within the same bucket"""
    state = await get_user_state()
    exercise_library = await get_exercise_library()
    
    old_ex = exercise_library.get(request.exercise_id)
    if not old_ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    alternatives = await get_exercises_for_bucket(
        old_ex["category"],
        request.equipment,
        state.week_mode,
        [request.exercise_id]
    )
    
    if not alternatives:
        raise HTTPException(status_code=400, detail="No alternatives available")
    
    new_ex = random.choice(alternatives)
    benchmarks = await get_benchmarks()
    protocol = await get_protocol_for_exercise(new_ex, "medium")
    load = await get_load_level(new_ex, "medium", benchmarks, request.equipment)
    
    return build_exercise_output(new_ex, protocol, load)

@api_router.post("/complete")
async def complete_session(feedback: SessionFeedback):
    """Mark session as completed and advance rotation"""
    state = await get_user_state()
    
    current_idx = BUCKET_ROTATION.index(state.next_priority_bucket)
    next_idx = (current_idx + 1) % len(BUCKET_ROTATION)
    next_bucket = BUCKET_ROTATION[next_idx]
    
    updates = {
        "next_priority_bucket": next_bucket
    }
    
    if feedback.feedback == "not_good":
        updates["cooldown_counter"] = 2
        updates["cooldown_override"] = False
    elif state.cooldown_counter > 0:
        updates["cooldown_counter"] = state.cooldown_counter - 1
    
    session = await db.sessions.find_one({"id": feedback.session_id})
    if session:
        exercise_ids = [ex["id"] for ex in session.get("exercises", [])]
        updates["last_session_exercises"] = exercise_ids
        
        if "kb_swing" in exercise_ids:
            updates["power_last_used"] = datetime.utcnow()
        
        if session.get("day_type") == "hard":
            updates["last_hard_day"] = True
        else:
            updates["last_hard_day"] = False
    
    await update_user_state(updates)
    
    await db.sessions.update_one(
        {"id": feedback.session_id},
        {"$set": {"completed": True, "feedback": feedback.feedback}}
    )
    
    return {"success": True, "next_priority_bucket": next_bucket}

@api_router.get("/history")
async def get_session_history(limit: int = 10):
    """Get recent session history"""
    sessions = await db.sessions.find(
        {"completed": True}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return sessions

@api_router.post("/reset")
async def reset_state():
    """Reset user state (for testing)"""
    await db.user_state.delete_many({})
    await db.sessions.delete_many({})
    return {"success": True, "message": "State reset"}

# ===========================
# ADMIN API ROUTES
# ===========================

@api_router.post("/admin/login")
async def admin_login(login: AdminLogin):
    """Admin login - returns token if password is correct"""
    if verify_admin(login.password):
        token = get_admin_token(login.password)
        return {"success": True, "token": token}
    raise HTTPException(status_code=401, detail="Invalid password")

@api_router.get("/admin/verify")
async def admin_verify(x_admin_token: str = Header(None)):
    """Verify admin token"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
    return {"success": True}

# Exercise CRUD
@api_router.post("/admin/exercises")
async def create_exercise(exercise: ExerciseCreate, x_admin_token: str = Header(None)):
    """Create a new exercise"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    existing = await db.exercises.find_one({"id": exercise.id})
    if existing:
        raise HTTPException(status_code=400, detail="Exercise ID already exists")
    
    await db.exercises.insert_one(exercise.dict())
    return {"success": True, "exercise": exercise.dict()}

@api_router.put("/admin/exercises/{exercise_id}")
async def update_exercise(exercise_id: str, updates: ExerciseUpdate, x_admin_token: str = Header(None)):
    """Update an existing exercise"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    existing = await db.exercises.find_one({"id": exercise_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    if update_dict:
        await db.exercises.update_one({"id": exercise_id}, {"$set": update_dict})
    
    updated = await db.exercises.find_one({"id": exercise_id}, {"_id": 0})
    return {"success": True, "exercise": updated}

@api_router.delete("/admin/exercises/{exercise_id}")
async def delete_exercise(exercise_id: str, x_admin_token: str = Header(None)):
    """Delete an exercise"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    result = await db.exercises.delete_one({"id": exercise_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    return {"success": True, "message": f"Exercise {exercise_id} deleted"}

# Protocol CRUD
@api_router.post("/admin/protocols")
async def create_protocol(protocol: ProtocolCreate, x_admin_token: str = Header(None)):
    """Create a new protocol"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    existing = await db.protocols.find_one({"id": protocol.id})
    if existing:
        raise HTTPException(status_code=400, detail="Protocol ID already exists")
    
    await db.protocols.insert_one(protocol.dict())
    return {"success": True, "protocol": protocol.dict()}

@api_router.put("/admin/protocols/{protocol_id}")
async def update_protocol(protocol_id: str, updates: ProtocolUpdate, x_admin_token: str = Header(None)):
    """Update an existing protocol"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    existing = await db.protocols.find_one({"id": protocol_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    if update_dict:
        await db.protocols.update_one({"id": protocol_id}, {"$set": update_dict})
    
    updated = await db.protocols.find_one({"id": protocol_id})
    return {"success": True, "protocol": updated}

@api_router.delete("/admin/protocols/{protocol_id}")
async def delete_protocol(protocol_id: str, x_admin_token: str = Header(None)):
    """Delete a protocol"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    result = await db.protocols.delete_one({"id": protocol_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return {"success": True, "message": f"Protocol {protocol_id} deleted"}

# Assign protocols to exercise
@api_router.put("/admin/exercises/{exercise_id}/protocols")
async def assign_protocols_to_exercise(exercise_id: str, protocol_ids: List[str], x_admin_token: str = Header(None)):
    """Assign specific protocols to an exercise (custom variations)"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    existing = await db.exercises.find_one({"id": exercise_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    await db.exercises.update_one(
        {"id": exercise_id},
        {"$set": {"custom_protocols": protocol_ids}}
    )
    
    updated = await db.exercises.find_one({"id": exercise_id}, {"_id": 0})
    return {"success": True, "exercise": updated}

@api_router.post("/admin/seed")
async def seed_data(x_admin_token: str = Header(None)):
    """Force re-seed the database with default data (WARNING: overwrites existing!)"""
    if not x_admin_token or not verify_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    await db.exercises.delete_many({})
    await db.protocols.delete_many({})
    await db.exercises.insert_many(DEFAULT_EXERCISES)
    await db.protocols.insert_many(DEFAULT_PROTOCOLS)
    
    return {"success": True, "message": f"Seeded {len(DEFAULT_EXERCISES)} exercises and {len(DEFAULT_PROTOCOLS)} protocols"}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Seed database on startup if empty"""
    await seed_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
