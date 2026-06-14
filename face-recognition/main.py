# Handles API requests and responses

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import numpy as np
import cv2

from recognizer import extract_embedding, serialize_embedding, find_match
from database import get_db, init_db, StudentsEmbeddings

app = FastAPI(title="Face Recognition") #Creates API application instance
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
    contents = await image.read()                 #reads uploaded file bytes
    np_arr = np.frombuffer(contents, np.uint8)    #Bytes -> Numpy array
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  #Array -> OpenCV image -> returns ndarray(image pixels)

    if img is None:
        raise HTTPException(400, "Invalid Image file")
    
    embedding = extract_embedding(img)
    if embedding is None:
        raise HTTPException(400, "No face detected in the image")
    
    #creates a row object for registered student
    record = StudentsEmbeddings(
        student_id = student_id,
        name = name,
        embedding = serialize_embedding(embedding),
        registered_at = datetime.utcnow()
    ) 

    db.merge(record) #Insert or update the embedding
    db.commit() #Save the changes to the database

    return  {"message" : "Student Registered", "student_id": student_id}

#Recognize a face
@app.post("/recognize")
async def recognize_face(
    image : UploadFile = File(...),
    db : Session = Depends(get_db),
):
    """
    Accepts an image from the scanner, extracts the face embedding,
    and returns the matching student or raise an exception
    """

    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(400, "Invalid image file")
    
    query_embedding = extract_embedding(img)
    if query_embedding is None:
        raise HTTPException(422, "No face detected in image")
    
    #Load the student embedding from the database
    students = db.query(StudentsEmbeddings).all()
    if not students:
        raise HTTPException(404, "No registered student in the database")
    
    #converts database objects into dictionaries
    student_list = [
        {
            "student_id" : s.student_id,
            "name" : s.name,
            "embedding" : s.embedding
        }
        for s in students
    ]
    
    match = find_match(query_embedding, student_list)

    if match:
        return {"status": "recognized", **match}
    else:
        return {"status": "unknown", "confidence": 0.0}