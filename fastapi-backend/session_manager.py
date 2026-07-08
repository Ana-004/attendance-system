#Timer Engine

import redis
import json
from datetime import datetime, timezone
from config import setting

r = redis.from_url(setting.REDIS_URL, decode_responses=True)  #Creates a redis connection object

SESSION_TTL_SECONDS = 60 * 60 * 8  # auto-expire session after 8 hours (Working hours in a day)

def _entry_key(student_id: str) -> str:
    return f"session:entry:{student_id}"

def _session_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def start_session(student_id:str) -> dict:
    """
    Called when student scans at Entry gate,
    Stores entry timestamp in Redis with a TTL of 8 hours,
    Returns error if session already active.
    """
    key  = _entry_key(student_id)

    if r.exists(key):
        existing = json.loads(r.get(key))
        return {
            "status" : "already_active",
            "message" : "Session already started",
            "entry_time" : existing["entry_time"] 
        }
    
    entry_time = datetime.now(timezone.utc).isoformat()
    payload = {
        "student_id" : student_id,
        "entry_time" : entry_time,
        "date" : _session_date()
    }

    r.setex(key, SESSION_TTL_SECONDS, json.dumps(payload))

    return {
        "status" : "session_started",
        "student_id" : student_id,
        "entry_time" : entry_time
    }

def end_session(student_id: str) -> dict:
    '''
    Called when student scans at EXIT gate,
    Calculates duration and returns whether attendance is counted.
    '''
    key = _entry_key(student_id)

    if not r.exists(key):
        return {
            "status" : "no_active_session",
            "message" : "No entry scan found for this student today"
        }
    
    session_data = json.loads(r.get(key))
    entry_time = datetime.fromisoformat(session_data["entry_time"])
    exit_time = datetime.now(timezone.utc)
    duration_min = int((exit_time - entry_time).total_seconds() /60)

    is_counted = duration_min >= settings.MIN_ATTENDANCE_MINUATES

    r.delete(key) #clear session from Redis

    return {
        "status" : "session_ended",
        "student_id" : student_id,
        "entry_time" : entry_time.isoformat(),
        "exit_time" : exit_time.isoformat(),
        "duration_min" : duration_min,
        "is_counted" : is_counted,
        "date" : session_data["date"]

    }

def get_active_session(student_id : str) -> dict | None:
    '''
    Return active session data if exist else None
    '''
    key = _entry_key(student_id)

    if not r.exist(key):
        return None
    
    return json.loads(r.get(key))

def get_all_active_session() -> dict:
    '''
    Return all current active sessions(for admin dashboard)
    '''
    keys = r.keys("session:entry:*")
    sessions = []

    for key in keys:
        data = r.get(key)
        if data:
            s= json.loads(data)
            entry_time = datetime.fromisoformat(s["entry_time"])
            elapsed = int((datetime.now(timezone.utc) - entry_time).total_seconds / 60)
            s["elapsed_min"] = elapsed >= settings.MIN_ATTENDANCE_MINUTES
            sessions.append(s)
            
    return sessions