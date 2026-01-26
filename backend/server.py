from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===========================
# EXERCISE LIBRARY (LOCKED)
# ===========================

EXERCISE_LIBRARY = {
    # SQUAT category
    "kb_goblet_squat": {
        "id": "kb_goblet_squat",
        "name": "KB Goblet Squat",
        "category": "squat",
        "equipment": ["home", "minimal"],
        "bilateral": True,
        "is_anchor": False
    },
    "single_kb_front_squat": {
        "id": "single_kb_front_squat",
        "name": "Single KB Front Squat",
        "category": "squat",
        "equipment": ["home", "minimal"],
        "bilateral": True,
        "is_anchor": True
    },
    "double_kb_front_squat": {
        "id": "double_kb_front_squat",
        "name": "Double KB Front Squat",
        "category": "squat",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": True
    },
    "kb_split_squat": {
        "id": "kb_split_squat",
        "name": "KB Split Squat",
        "category": "squat",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": True
    },
    "kb_rfess": {
        "id": "kb_rfess",
        "name": "KB Rear Foot Elevated Split Squat",
        "category": "squat",
        "equipment": ["home"],
        "bilateral": False,
        "is_anchor": True
    },
    "atg_split_squat": {
        "id": "atg_split_squat",
        "name": "ATG Split Squat",
        "category": "squat",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": False,
        "is_anchor": False
    },
    "rear_leg_assisted_shrimp": {
        "id": "rear_leg_assisted_shrimp",
        "name": "Rear Leg Assisted Shrimp",
        "category": "squat",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": False,
        "is_anchor": False
    },
    "kb_lunge": {
        "id": "kb_lunge",
        "name": "KB Lunge",
        "category": "squat",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "bw_lunge": {
        "id": "bw_lunge",
        "name": "Bodyweight Lunge",
        "category": "squat",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": False,
        "is_anchor": False
    },
    
    # HINGE category
    "kb_sumo_deadlift": {
        "id": "kb_sumo_deadlift",
        "name": "KB Sumo Deadlift",
        "category": "hinge",
        "equipment": ["home", "minimal"],
        "bilateral": True,
        "is_anchor": False
    },
    "kb_suitcase_deadlift": {
        "id": "kb_suitcase_deadlift",
        "name": "KB Suitcase Deadlift",
        "category": "hinge",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "single_leg_kb_deadlift": {
        "id": "single_leg_kb_deadlift",
        "name": "Single Leg KB Deadlift",
        "category": "hinge",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": True
    },
    "hip_thrust": {
        "id": "hip_thrust",
        "name": "Hip Thrust",
        "category": "hinge",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": True
    },
    "single_leg_hip_thrust": {
        "id": "single_leg_hip_thrust",
        "name": "Single Leg Hip Thrust",
        "category": "hinge",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": False,
        "is_anchor": False
    },
    "band_hip_thrust": {
        "id": "band_hip_thrust",
        "name": "Band Hip Thrust",
        "category": "hinge",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": False
    },
    "kb_swing": {
        "id": "kb_swing",
        "name": "KB Swing",
        "category": "hinge",
        "equipment": ["home", "minimal"],
        "bilateral": True,
        "is_anchor": False,
        "is_power": True
    },
    
    # PUSH category
    "pushup": {
        "id": "pushup",
        "name": "Push-up",
        "category": "push",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": True
    },
    "kb_press_single": {
        "id": "kb_press_single",
        "name": "KB Military Press (Single)",
        "category": "push",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": True
    },
    "kb_press_double": {
        "id": "kb_press_double",
        "name": "KB Military Press (Double)",
        "category": "push",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": True
    },
    "floor_press_single": {
        "id": "floor_press_single",
        "name": "Floor Press (Single)",
        "category": "push",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "floor_press_double": {
        "id": "floor_press_double",
        "name": "Floor Press (Double)",
        "category": "push",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": False
    },
    "diamond_pushup": {
        "id": "diamond_pushup",
        "name": "Diamond Push-up",
        "category": "push",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": False
    },
    "deficit_pushup": {
        "id": "deficit_pushup",
        "name": "Deficit Push-up",
        "category": "push",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": False
    },
    "sfg_plank": {
        "id": "sfg_plank",
        "name": "SFG Plank",
        "category": "push",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": False
    },
    "pushup_plank": {
        "id": "pushup_plank",
        "name": "Push-up Plank",
        "category": "push",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": False
    },
    
    # PULL category
    "pullup": {
        "id": "pullup",
        "name": "Pull-up",
        "category": "pull",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": True
    },
    "chinup": {
        "id": "chinup",
        "name": "Chin-up",
        "category": "pull",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": True
    },
    "australian_pullup": {
        "id": "australian_pullup",
        "name": "Australian Pull-up",
        "category": "pull",
        "equipment": ["home"],
        "bilateral": True,
        "is_anchor": False
    },
    "kb_row": {
        "id": "kb_row",
        "name": "KB Row",
        "category": "pull",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "bw_batwing_hold": {
        "id": "bw_batwing_hold",
        "name": "Bodyweight Batwing Hold",
        "category": "pull",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": False
    },
    
    # CARRY and LOCOMOTION
    "farmer_carry": {
        "id": "farmer_carry",
        "name": "Farmer Carry",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": True,
        "is_anchor": True
    },
    "suitcase_carry": {
        "id": "suitcase_carry",
        "name": "Suitcase Carry",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "rack_carry": {
        "id": "rack_carry",
        "name": "Rack Carry",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "overhead_carry": {
        "id": "overhead_carry",
        "name": "Overhead Carry",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "bottom_up_carry": {
        "id": "bottom_up_carry",
        "name": "Bottom Up Carry",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "stationary_march_goblet": {
        "id": "stationary_march_goblet",
        "name": "Stationary March (Goblet)",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": True,
        "is_anchor": False
    },
    "stationary_march_rack": {
        "id": "stationary_march_rack",
        "name": "Stationary March (Rack)",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "stationary_march_overhead": {
        "id": "stationary_march_overhead",
        "name": "Stationary March (Overhead)",
        "category": "carry",
        "equipment": ["home", "minimal"],
        "bilateral": False,
        "is_anchor": False
    },
    "bear_crawl": {
        "id": "bear_crawl",
        "name": "Bear Crawl",
        "category": "crawl",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": False
    },
    "tiger_crawl": {
        "id": "tiger_crawl",
        "name": "Tiger Crawl",
        "category": "crawl",
        "equipment": ["home", "minimal", "bodyweight"],
        "bilateral": True,
        "is_anchor": False
    },
}

# Priority bucket rotation order
BUCKET_ROTATION = ["squat", "pull", "hinge", "push"]

# Default protocols by exercise type
PROTOCOLS = {
    "kettlebell_strength": [
        {"name": "Ladder 1-2-3", "sets": "3-5 ladders", "reps": "1,2,3", "rest": "60-90s"},
        {"name": "Ladder 1-2-3-4-5", "sets": "2-3 ladders", "reps": "1,2,3,4,5", "rest": "60-90s"},
        {"name": "Sets Across", "sets": "3-5", "reps": "5", "rest": "60-90s"},
        {"name": "Density Block", "sets": "AMRAP", "reps": "3-5", "rest": "10 min total"},
    ],
    "bodyweight_strength": [
        {"name": "Sets Across", "sets": "3-5", "reps": "5-8", "rest": "60-90s"},
        {"name": "Ladder 1-2-3", "sets": "3-5 ladders", "reps": "1,2,3", "rest": "60s"},
        {"name": "Total Reps Target", "sets": "As needed", "reps": "Total 25-50", "rest": "As needed"},
    ],
    "carry": [
        {"name": "Distance", "sets": "3-4", "reps": "20-40m", "rest": "60s"},
        {"name": "Time", "sets": "3-4", "reps": "30-60s", "rest": "60s"},
    ],
    "crawl": [
        {"name": "Distance", "sets": "3-5", "reps": "10-20m", "rest": "30-60s"},
        {"name": "Time", "sets": "3-5", "reps": "20-30s", "rest": "30-60s"},
    ],
    "power": [
        {"name": "On the Minute", "sets": "10-15", "reps": "10", "rest": "Top of min"},
        {"name": "Sets Across", "sets": "5-10", "reps": "10-15", "rest": "60s"},
    ],
    "easy": [
        {"name": "Light Practice", "sets": "2-3", "reps": "3-5", "rest": "90s"},
        {"name": "Movement Flow", "sets": "2-3", "reps": "5", "rest": "As needed"},
    ],
}

# ===========================
# PYDANTIC MODELS
# ===========================

class QuestionnaireInput(BaseModel):
    feeling: Literal["bad", "ok", "great"]
    sleep: Literal["bad", "good"]
    pain: Literal["none", "present"]
    time_available: Literal["20-30", "30-45", "45-60"]
    equipment: Literal["home", "minimal", "bodyweight"]
    override_bucket: Optional[str] = None  # Allow manual focus override

class ExerciseOutput(BaseModel):
    id: str
    name: str
    category: str
    load_level: str
    protocol: str
    sets: str
    reps: str
    rest: str
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

class SessionFeedback(BaseModel):
    session_id: str
    feedback: Literal["good", "not_good"]

class SwapRequest(BaseModel):
    session_id: str
    exercise_id: str
    equipment: str

# ===========================
# HELPER FUNCTIONS
# ===========================

async def get_user_state() -> UserState:
    """Get or create user state"""
    state = await db.user_state.find_one({"id": "user_state"})
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
    bench = await db.benchmarks.find_one({"id": "benchmarks"})
    if bench:
        return Benchmarks(**bench)
    new_bench = Benchmarks()
    await db.benchmarks.insert_one(new_bench.dict())
    return new_bench

def get_exercises_for_bucket(bucket: str, equipment: str, week_mode: str, exclude_ids: List[str] = []) -> List[dict]:
    """Get available exercises for a bucket filtered by equipment and week mode"""
    exercises = []
    for ex_id, ex in EXERCISE_LIBRARY.items():
        if ex["category"] != bucket:
            continue
        if equipment not in ex["equipment"]:
            continue
        if ex_id in exclude_ids:
            continue
        # Week mode filtering
        if week_mode == "A" and not ex.get("bilateral", True):
            # A = bilateral week, prefer bilateral but allow single-leg
            pass
        elif week_mode == "B" and ex.get("bilateral", True) and bucket in ["squat", "hinge"]:
            # B = single-leg week for squat/hinge, prefer unilateral
            pass
        exercises.append(ex)
    return exercises

def determine_day_type(questionnaire: QuestionnaireInput, state: UserState) -> str:
    """Determine day type based on questionnaire and state"""
    # Check for automatic EASY conditions
    if questionnaire.pain == "present":
        return "easy"
    if questionnaire.feeling == "bad":
        return "easy"
    if questionnaire.sleep == "bad":
        return "easy"
    if state.cooldown_counter > 0:
        return "easy"
    if state.last_hard_day:
        return "easy"
    
    # Check for HARD conditions
    if questionnaire.feeling == "great" and questionnaire.sleep == "good" and questionnaire.pain == "none":
        # Can be MEDIUM or HARD
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
    
    # Check frequency
    if state.power_last_used:
        days_since_power = (datetime.utcnow() - state.power_last_used).days
        if state.power_frequency == "weekly" and days_since_power < 7:
            return False
        if state.power_frequency == "fortnightly" and days_since_power < 14:
            return False
    
    return True

def select_exercise_from_bucket(bucket: str, equipment: str, week_mode: str, exclude_ids: List[str], prefer_anchor: bool = True) -> Optional[dict]:
    """Select a single exercise from a bucket"""
    exercises = get_exercises_for_bucket(bucket, equipment, week_mode, exclude_ids)
    
    if not exercises:
        # Fallback: try without week mode preference
        for ex_id, ex in EXERCISE_LIBRARY.items():
            if ex["category"] == bucket and equipment in ex["equipment"] and ex_id not in exclude_ids:
                exercises.append(ex)
    
    if not exercises:
        return None
    
    # Sort by anchor preference
    if prefer_anchor:
        anchors = [ex for ex in exercises if ex.get("is_anchor", False)]
        if anchors:
            exercises = anchors
    
    # Week mode preference
    if week_mode == "A":
        bilateral = [ex for ex in exercises if ex.get("bilateral", True)]
        if bilateral:
            exercises = bilateral
    elif week_mode == "B" and bucket in ["squat", "hinge"]:
        unilateral = [ex for ex in exercises if not ex.get("bilateral", True)]
        if unilateral:
            exercises = unilateral
    
    return random.choice(exercises) if exercises else None

def get_protocol_for_exercise(ex: dict, day_type: str, equipment: str) -> dict:
    """Get appropriate protocol for an exercise"""
    category = ex["category"]
    
    if day_type == "easy":
        protocols = PROTOCOLS["easy"]
    elif category == "carry":
        protocols = PROTOCOLS["carry"]
    elif category == "crawl":
        protocols = PROTOCOLS["crawl"]
    elif ex.get("is_power"):
        protocols = PROTOCOLS["power"]
    elif equipment == "bodyweight" or category in ["push"] and ex["id"] in ["pushup", "diamond_pushup", "deficit_pushup"]:
        protocols = PROTOCOLS["bodyweight_strength"]
    else:
        protocols = PROTOCOLS["kettlebell_strength"]
    
    return random.choice(protocols)

def get_load_level(ex: dict, day_type: str, benchmarks: Benchmarks, equipment: str) -> str:
    """Determine load level for an exercise"""
    if equipment == "bodyweight":
        if day_type == "easy":
            return "Slow tempo"
        return "Standard"
    
    if day_type == "easy":
        return "Light (60-70%)"
    elif day_type == "medium":
        return "Moderate (75-85%)"
    else:
        return "Heavy (85-95%)"

def generate_session(questionnaire: QuestionnaireInput, state: UserState, benchmarks: Benchmarks, is_reroll: bool = False) -> SessionOutput:
    """Generate a training session"""
    day_type = determine_day_type(questionnaire, state)
    equipment = questionnaire.equipment
    week_mode = state.week_mode
    # Use override bucket if provided, otherwise use state
    priority_bucket = questionnaire.override_bucket if questionnaire.override_bucket else state.next_priority_bucket
    
    # Determine number of exercises based on time
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
    else:  # 45-60
        max_exercises = 5
        include_carry = True
        include_crawl = True
        secondary_buckets = 3
    
    exercises = []
    used_ids = state.last_session_exercises[:1] if not is_reroll else []  # Avoid same first exercise
    
    # 1. Priority bucket exercise (first)
    primary_ex = select_exercise_from_bucket(priority_bucket, equipment, week_mode, used_ids, prefer_anchor=True)
    if primary_ex:
        protocol = get_protocol_for_exercise(primary_ex, day_type, equipment)
        load = get_load_level(primary_ex, day_type, benchmarks, equipment)
        exercises.append(ExerciseOutput(
            id=primary_ex["id"],
            name=primary_ex["name"],
            category=primary_ex["category"],
            load_level=load,
            protocol=protocol["name"],
            sets=protocol["sets"],
            reps=protocol["reps"],
            rest=protocol["rest"],
            notes="Priority" if primary_ex.get("is_anchor") else ""
        ))
        used_ids.append(primary_ex["id"])
    
    # 2. Secondary buckets
    other_buckets = [b for b in BUCKET_ROTATION if b != priority_bucket]
    random.shuffle(other_buckets)
    
    for i, bucket in enumerate(other_buckets[:secondary_buckets]):
        ex = select_exercise_from_bucket(bucket, equipment, week_mode, used_ids, prefer_anchor=True)
        if ex:
            # Check if it's a swing and if allowed
            if ex.get("is_power") and not can_use_power(state, day_type, questionnaire):
                # Try to get a non-power exercise
                ex = select_exercise_from_bucket(bucket, equipment, week_mode, used_ids + ["kb_swing"], prefer_anchor=True)
                if not ex:
                    continue
            
            protocol = get_protocol_for_exercise(ex, day_type, equipment)
            load = get_load_level(ex, day_type, benchmarks, equipment)
            exercises.append(ExerciseOutput(
                id=ex["id"],
                name=ex["name"],
                category=ex["category"],
                load_level=load,
                protocol=protocol["name"],
                sets=protocol["sets"],
                reps=protocol["reps"],
                rest=protocol["rest"]
            ))
            used_ids.append(ex["id"])
    
    # 3. Carry (if time allows)
    if include_carry and len(exercises) < max_exercises:
        carry_ex = select_exercise_from_bucket("carry", equipment, week_mode, used_ids)
        if carry_ex:
            protocol = get_protocol_for_exercise(carry_ex, day_type, equipment)
            exercises.append(ExerciseOutput(
                id=carry_ex["id"],
                name=carry_ex["name"],
                category=carry_ex["category"],
                load_level=get_load_level(carry_ex, day_type, benchmarks, equipment),
                protocol=protocol["name"],
                sets=protocol["sets"],
                reps=protocol["reps"],
                rest=protocol["rest"],
                notes="Finisher"
            ))
            used_ids.append(carry_ex["id"])
    
    # 4. Crawl (if time allows and 45-60 min)
    if include_crawl and len(exercises) < max_exercises:
        crawl_ex = select_exercise_from_bucket("crawl", equipment, week_mode, used_ids)
        if crawl_ex:
            protocol = get_protocol_for_exercise(crawl_ex, day_type, equipment)
            exercises.append(ExerciseOutput(
                id=crawl_ex["id"],
                name=crawl_ex["name"],
                category=crawl_ex["category"],
                load_level="Bodyweight",
                protocol=protocol["name"],
                sets=protocol["sets"],
                reps=protocol["reps"],
                rest=protocol["rest"],
                notes="Support"
            ))
    
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
    return list(EXERCISE_LIBRARY.values())

@api_router.get("/exercises/{category}")
async def get_exercises_by_category(category: str):
    """Get exercises by category"""
    return [ex for ex in EXERCISE_LIBRARY.values() if ex["category"] == category]

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
    """Update user settings (week mode, power frequency)"""
    state = await get_user_state()
    update_dict = {}
    
    if updates.week_mode is not None:
        update_dict["week_mode"] = updates.week_mode
        update_dict["week_mode_last_changed"] = datetime.utcnow()
    
    if updates.power_frequency is not None:
        update_dict["power_frequency"] = updates.power_frequency
    
    if update_dict:
        await update_user_state(update_dict)
    
    return await get_user_state()

@api_router.post("/generate", response_model=SessionOutput)
async def generate_session_route(questionnaire: QuestionnaireInput):
    """Generate a training session based on questionnaire"""
    state = await get_user_state()
    benchmarks = await get_benchmarks()
    
    # Auto-toggle week mode every 7 days
    days_since_mode_change = (datetime.utcnow() - state.week_mode_last_changed).days
    if days_since_mode_change >= 7:
        new_mode = "B" if state.week_mode == "A" else "A"
        await update_user_state({
            "week_mode": new_mode,
            "week_mode_last_changed": datetime.utcnow()
        })
        state = await get_user_state()
    
    session = generate_session(questionnaire, state, benchmarks)
    
    # Store session
    await db.sessions.insert_one(session.dict())
    
    # Check if we need to set cooldown
    if questionnaire.pain == "present" or questionnaire.feeling == "bad" or questionnaire.sleep == "bad":
        await update_user_state({"cooldown_counter": 2})
    
    return session

@api_router.post("/reroll", response_model=SessionOutput)
async def reroll_session(questionnaire: QuestionnaireInput):
    """Reroll the session (same rules, different expressions)"""
    state = await get_user_state()
    benchmarks = await get_benchmarks()
    
    session = generate_session(questionnaire, state, benchmarks, is_reroll=True)
    
    # Store session (replace latest)
    await db.sessions.delete_one({"id": session.id})
    await db.sessions.insert_one(session.dict())
    
    return session

@api_router.post("/swap")
async def swap_exercise(request: SwapRequest):
    """Swap a single exercise within the same bucket"""
    state = await get_user_state()
    
    # Find the exercise to swap
    old_ex = EXERCISE_LIBRARY.get(request.exercise_id)
    if not old_ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Get alternatives
    alternatives = get_exercises_for_bucket(
        old_ex["category"],
        request.equipment,
        state.week_mode,
        [request.exercise_id]
    )
    
    if not alternatives:
        raise HTTPException(status_code=400, detail="No alternatives available")
    
    new_ex = random.choice(alternatives)
    benchmarks = await get_benchmarks()
    protocol = get_protocol_for_exercise(new_ex, "medium", request.equipment)
    load = get_load_level(new_ex, "medium", benchmarks, request.equipment)
    
    return ExerciseOutput(
        id=new_ex["id"],
        name=new_ex["name"],
        category=new_ex["category"],
        load_level=load,
        protocol=protocol["name"],
        sets=protocol["sets"],
        reps=protocol["reps"],
        rest=protocol["rest"]
    )

@api_router.post("/complete")
async def complete_session(feedback: SessionFeedback):
    """Mark session as completed and advance rotation"""
    state = await get_user_state()
    
    # Advance priority bucket
    current_idx = BUCKET_ROTATION.index(state.next_priority_bucket)
    next_idx = (current_idx + 1) % len(BUCKET_ROTATION)
    next_bucket = BUCKET_ROTATION[next_idx]
    
    updates = {
        "next_priority_bucket": next_bucket
    }
    
    # Handle feedback
    if feedback.feedback == "not_good":
        updates["cooldown_counter"] = 2
    elif state.cooldown_counter > 0:
        updates["cooldown_counter"] = state.cooldown_counter - 1
    
    # Get session to check if power was used
    session = await db.sessions.find_one({"id": feedback.session_id})
    if session:
        exercise_ids = [ex["id"] for ex in session.get("exercises", [])]
        updates["last_session_exercises"] = exercise_ids
        
        if "kb_swing" in exercise_ids:
            updates["power_last_used"] = datetime.utcnow()
        
        # Track hard day
        if session.get("day_type") == "hard":
            updates["last_hard_day"] = True
        else:
            updates["last_hard_day"] = False
    
    await update_user_state(updates)
    
    # Mark session as completed in DB
    await db.sessions.update_one(
        {"id": feedback.session_id},
        {"$set": {"completed": True, "feedback": feedback.feedback}}
    )
    
    return {"success": True, "next_priority_bucket": next_bucket}

@api_router.get("/history")
async def get_session_history(limit: int = 10):
    """Get recent session history"""
    sessions = await db.sessions.find(
        {"completed": True}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return sessions

@api_router.post("/reset")
async def reset_state():
    """Reset user state (for testing)"""
    await db.user_state.delete_many({})
    await db.sessions.delete_many({})
    return {"success": True, "message": "State reset"}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
