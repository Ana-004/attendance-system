from sqlalchemy.orm import Session
from datetime import datetime, timezone
from database import AttendanceSession, AttendanceRecord, Student
import httpx   # handles communication request to external APIs
from config import Settings

def record_sessioon(db: Session, session_result: dict):
    '''
    Persists a completed session to postgreSQL
    and create an attendance record if counted
    '''

    session = AttendanceSession(
        student_id = session_result["student_id"]
        entry_time = datetime.fromisoformat(session_result["entry_time"])
        exit_time = datetime.fromisoformat(session_result["exit_time"])
        duration_min = session_result["duration_min"]
        is_counted = session_result["is_counted"]
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



