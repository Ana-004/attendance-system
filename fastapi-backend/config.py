"""
Configuration file which will store all the necessary settings 
and connection information that the application will use such as
DATABASE_URL, face-recognition_URL, Redis_URL, etc
"""

from pathlib import Path
from pydantic_settings import BaseSettings   #used for combining configuration and environment variable loading

BASE_DIR = Path(__file__).resolve().parent.parent #Goes one level higher into the directory tree (the folder containing fastapi-backend)

class Settings(BaseSettings):
    DATABASE_URL: str 
    REDIS_URL: str 
    FACE_RECOGNITION_URL: str
    MIN_ATTENDANCE_MINUTES: int = 20
    SYNC_API_URL: str

    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()