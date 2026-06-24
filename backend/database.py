from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    description = Column(Text)
    skills_required = Column(JSON)
    seniority = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String)
    name = Column(String)
    github_username = Column(String)
    avatar_url = Column(String)
    bio = Column(Text)
    location = Column(String)
    public_repos = Column(Integer)
    followers = Column(Integer)
    total_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    collaboration_score = Column(Float, default=0.0)
    learning_velocity_score = Column(Float, default=0.0)
    code_quality_score = Column(Float, default=0.0)
    skill_alignment_score = Column(Float, default=0.0)
    fraud_score = Column(Float, default=0.0)
    fraud_risk = Column(String, default="Low")
    fraud_signals = Column(JSON)
    explanation = Column(Text)
    skill_proofs = Column(JSON)
    skill_gaps = Column(JSON)
    top_repos = Column(JSON)
    languages = Column(JSON)
    interview_questions = Column(JSON)
    rank = Column(Integer)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
