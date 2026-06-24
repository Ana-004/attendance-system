#Timer Engine

import redis
import json
from datetime import datetime, timezone
from config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)  #Creates a redis connection object

SESSION_TTL_SECONDS = 60 * 60 * 8  # auto-expire session after 8 hours (Working hours in a day)

def _entry_key(student_id: str) -> str:
    return f"sessio:entry:{student_id}"

def _session_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def start_session(student_id:str) -> dict:
    """
    Called when student scans at Entry gate,
    Stores entry timestamp in Redis with a TTl of 8 hours,
    Returns error if session already active.
    """