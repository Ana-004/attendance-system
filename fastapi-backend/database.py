from sqlalchemy import(
    create_engine, Column, String, DateTime, Integer, Boolean, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
from config import settings

engine = create_engine(settings.DATABASE_URL)   #Create a connection between python and the database
SessionLocal = sessionmaker(bind=engine)    #facilitate interaction with the database (creating sessions)
Base = declarative_base()  #Base Class for all database models(allows python classes to become database tables)

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    course = Column(String)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    #relationship() connect tables together
    sessions = relationship("AttendanceSession", back_populates="student")
    """
    realationship() :  create a link to another table
    back_populates : specify the attribute inthe related
    db model that will have reverse relationship.
    update one side, the other side updates automatically
    """

class AttendanceSession(Base):
    """This stores every student entry and exit details and whether the session is counted towards attendance"""

    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey("students.student_id"), nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    is_counted = Column(Boolean, default=False) # True if >= 20 minutes
    date = Column(String, nullable=False)

    student = relationship("Student", back_populates="sessions")


class AttendanceRecord(Base):
    """This stores the final attendance result"""

    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey("students.student_id"), nullable=False)
    date = Column(String, nullable=False)
    status = Column(String, default="present")
    duration_min = Column(Integer, nullable=True)
    marked_at = Column(DateTime, default=datetime.now(timezone.utc))

def get_db():
    """yields A database session, ensuring it's properly closed after use"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database by creating all tables"""
    Base.metadata.create_all(bind=engine)