'''
Manage all API routes for fastapibackend
'''

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import httpx

#importing modules from different files 
from config import setting
from database import get_db, init_db, Student
from session_manager import start_session, end_session, get_active_session, get_all_active_session
from attendance import record_session, get_student_attendance, get_attendance_summary, push_to_cloud


app = FastAPI(title="Attendance System Backend", description = "Backend API for Attendance System", version="1.0.0")

@app.on_event("startup")
def startup_event():
    init_db()

#Health
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "fastapi-backend", "timestamp": datetime.now(timezone.utc)}

#Enrty Scan
@app.post("/scan/entry")
async def entry_scan(
    image : UploadFile = File(...),
    background_tasks : BackgroundTasks = BackgroundTasks(),
    db : Session = Depends(get_db)
):
    '''
    Called by entry scanner:
    1. Sends image to the face-recognition service
    2. Get students id
    3. Start session timer in Redis
    '''

    image_bytes = await image.read()

    #call face-regonition service 
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(
                f"{setting.FACE_RECOGNITION_URL}/recognize",
                files = {"image" : (image.filename, image_bytes, image.content_type)}
            )
            result = resp.json()
        except Exception as e:
            raise HTTPException(503, "Face Recognition service unavailable")
    
    if result.get("status") != "recognized":
        return {"status" : "unknown", "message" : "Face not recognized"}
    
    student_id = result["student_id"]
    confidence = result["confidence"]

    #Check student exist in original DB
    student = db.query(Student).filter_by(student_id = student_id).first()
    if not student:
        raise HTTPException(404, f"Student {student_id} not found in database")
    
    #start_session starts session timer in Redis
    session = start_session(student_id)

    return {
        "status" : session["status"], 
        "student_id" : student_id,
        "student_name" : student.name, 
        "confidence" : confidence,
        "entry_time" : session.get("entry_time"),
        "message" : f"Welcome {student.name}! Timer Started"
    }

#Exit Scan
@app.post("/scan/exit")
async def exit_scan(
    image : UploadFile = File(...),
    background_tasks : BackgroundTasks = BackgroundTasks(),
    db : Session = Depends(get_db)
):
    '''
    Called by the exit scanner:
    1. Recognize the face
    2. Stops session timer
    3. Marks attendance if duration>=20 minutes
    4. Pushes summary to the cloud in background
    '''
    image_bytes = await image.read()

    #Call face-recognition service
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(
                f"{setting.FACE_RECOGNITION_URL}/recognize",
                files = {"image" : (image.filename, image_bytes, image.content_type)}
            )
            result = resp.json()
        except Exception as e:
            raise HTTPException(503, "Face Recognition service unavailable")
    
    if result.get("status") != "recognized":
        return {"status" : "unknown", "message" : "Face not recognized"}
    
    student_id = result["student_id"]

    #Check student exist in original DB
    student = db.query(Student).filter_by(student_id = student_id).first()
    if not student:
        raise HTTPException(404, f"Student {student_id} not found in database")
    
    #end_session stops session timer in Redis
    session_result = end_session(student_id)

    if session_result["status"] == "no_active_session":
        return {
            "status" : "no_entry",
            "message" : "No entry scan found for this student. Please use the entry gate first."
        }
    
    #Save to PostgreSQL
    record_session(db, session_result)

    #Push to Cloud (No sensitive information)
    background_tasks.add_task(push_to_cloud, session_result)

    attendance_msg = (
        f"Attendance marked!"
        if session_result["is_counted"]
        else f"Not counted - only {session_result["duration_min"]} min (need {setting.MIN_ATTENDANCE_MINUTES} min)"
    )

    return {
        "status" : "session_ended", 
        "student_id" : student_id,
        "student_name" : student.name, 
        "duration_minutes" : session_result["duration_min"],
        "is_counted" : session_result["is_counted"],
        "message" : attendance_msg
    }

#Student Attendance Posrtal API
@app.get("/attendance/{student_id}")
def student_attendance(student_id: str, db: Session = Depends(get_db)):
    '''
    Returns full attendance history for a student
    '''

    student = db.query(Student).filter_by(student_id = student_id).first()
    if not student:
        raise HTTPException(404, "Student Not found in database")
    
    records = get_student_attendance(db, student_id)
    summary = get_attendance_summary(db, student_id)

    return {
        "student" : {"id" : student.student_id, "name" : student.name},
        "records" : records,
        "summary" : summary
    }

#Active Sessions (for admin)
@app.get("/sessions/active")
def active_sessions():
    '''
    Return all students with active session (entry scanned but not exit)
    '''
    return {
        "active_session" : get_all_active_session()
    }