from sqlalchemy import create_engine, Column, String, LargeBinary, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL) #Create a connection with the database
SessionLocal = sessionmaker(bind=engine) #facilitate interaction with the database (creating sessions)
Base = declarative_base() #Base Class for all database models(allows python classes to become database tables)

class StudentsEmbeddings(Base):
    __tablename__ = "students_embeddings"

    student_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=False) #serialized numpy array
    registered_at = Column(DateTime)

def get_db():
    """Yields a database session, ensuring it's properly closed after use"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database by creating all tables"""
    Base.metadata.create_all(bind=engine)