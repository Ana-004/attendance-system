from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import numpy as np
import cv2

from recognizer import extract_embedding, serialize_embedding, find_match
from database import get_db, init_db, StudentsEmbeddings

app = FastAPI(title="Face Recognition")
@app.on_event("startup")
def startup():
    """Initialize the database when the application starts"""
    init_db()

#Health Check
@app.get("/health")
def health():
    """Endpoint to check if the application is running properly"""
    return {"statuse" : "ok", "service" : "face-recognition"}

#Register a new student face
@app.post("/register")
async def register_student(
    student_id : str, 
    name : str,
    image : UploadFile = File(...),
    db : Session = Depends(get_db)
):
    """
    Accepts a student photo, extracts face embedding,
    and stores it in the database.
    """
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(400, "Invalid Image file")
    
    embedding = extract_embedding(img)
    if embedding is None:
        raise HTTPException(400, "No face detected in the image")
    
    record = StudentsEmbeddings(
        student_id = student_id,
        name = name,
        embedding = serialize_embedding(embedding),
        registered_at = datetime.utcnow()
    )

    db.merge(record) #Insert or update the embedding
    db.commit() #Save the changes to the database

    return  {"message" : "Student Registered", "student_id": student_id}
