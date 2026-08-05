from sqlalchemy.orm import Session
from datetime import datetime, timezone
from database import AttendanceSession, AttendanceRecord, Student
import httpx   # handles communication request to external APIs
from config import settings

def record_session(db: Session, session_result: dict):
    '''
    Persists a completed session to postgreSQL
    and create an attendance record if counted
    '''

    session = AttendanceSession(
        student_id = session_result["student_id"],
        entry_time = datetime.fromisoformat(session_result["entry_time"]),
        exit_time = datetime.fromisoformat(session_result["exit_time"]),
        duration_min = session_result["duration_min"],
        is_counted = session_result["is_counted"],
        date = session_result["date"]
    )

    db.add(session)
    
    if session_result["is_counted"]:
        existing = db.query(AttendanceRecord).filter_by(
            student_id = session_result["student_id"],
            date = session_result["date"]
        ).first()

        if not existing:
            record = AttendanceRecord(
                student_id = session_result["student_id"],
                date = session_result["date"],
                status = "present",
                duration_min = session_result["duration_min"],
                marked_at = datetime.now(timezone.utc)
            )

            db.add(record)
        
    db.commit()

def get_student_attendance(db: Session, student_id: str) -> list[dict]:
    '''
    Return all attendance record for a student'''

    records = db.query(AttendanceRecord).filter_by(
        student_id = student_id
    ).order_by(AttendanceRecord.date.desc()).all

    return [
        {
            "date" : r.date,
            "status" : r.status,
            "duration_min" : r.duration_min,
            "marked_at" : r.marked_at.isoformat()
        }
        for r in records
    ]

def get_attendance_summary(db : Session, student_id: str) ->dict:
    '''
    Return present count and percentage for a student
    '''

    records = db.query(AttendanceRecord).filter_by(student_id = student_id).all()
    total = len(records)
    present = sum(1 for r in records if r.status=="present")
    percentage = round((present/total *100), 1) if total > 0 else 0.0

    return {
        "student_id" : student_id,
        "total_days" : total,
        "present_days" : present,
        "percentage" : percentage
    }

async def push_to_cloud(session_result: dict):
    '''
    Push attendance summary to cloud sync-api
    (send only the necessary information to a cloud server, *no biometrics)
    '''

    if not session_result.get("is_counted"):
        return
    
    payload = {
        "student_id" : session_result["student_id"],
        "date" : session_result["date"],
        "status" : "present",
        "duration_min" : session_result["duration_min"]
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:  #creates an asynchronous HTTP client
            await client.post(
                f"{settings.SYNC_API_URL}/sync/attendance",
                json=payload
            )
    except Exception as e:
        print(f"Cloud sync failed (non-critical) : {e}")