from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import threading
import os

from database import init_db, get_db, Job, Candidate
from agents.pipeline import run_full_pipeline

app = FastAPI(title="TalentGPT API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job status tracker
job_status = {}

@app.on_event("startup")
def startup():
    init_db()


# ── Request Models ────────────────────────────────────────────────

class CreateJobRequest(BaseModel):
    title: str
    jd_text: str
    github_usernames: list[str]


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ── Routes ────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "TalentGPT API is running 🚀", "version": "1.0.0"}


@app.post("/api/v1/jobs", response_model=JobResponse)
def create_job(req: CreateJobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new hiring job and start the analysis pipeline."""
    job_id = str(uuid.uuid4())

    # Save job to DB
    job = Job(
        id=job_id,
        title=req.title,
        description=req.jd_text,
        status="processing"
    )
    db.add(job)
    db.commit()

    job_status[job_id] = {
        "status": "processing",
        "progress": 0,
        "total": len(req.github_usernames),
        "message": "Pipeline started..."
    }

    # Run pipeline in background thread
    def run_and_save():
        try:
            job_status[job_id]["message"] = "Analyzing job description..."
            result = run_full_pipeline(req.jd_text, req.github_usernames)

            # Save candidates to DB
            new_db = next(get_db())
            try:
                for i, cand_result in enumerate(result["candidates"]):
                    gd = cand_result["github_data"]
                    sc = cand_result["scores"]
                    fr = cand_result["fraud_result"]

                    candidate = Candidate(
                        id=str(uuid.uuid4()),
                        job_id=job_id,
                        name=gd.get("name", gd.get("username")),
                        github_username=gd.get("username"),
                        avatar_url=gd.get("avatar_url", ""),
                        bio=gd.get("bio", ""),
                        location=gd.get("location", ""),
                        public_repos=gd.get("public_repos", 0),
                        followers=gd.get("followers", 0),
                        total_score=sc["total_score"],
                        technical_score=sc["technical_score"],
                        collaboration_score=sc["collaboration_score"],
                        learning_velocity_score=sc["learning_velocity_score"],
                        code_quality_score=sc["code_quality_score"],
                        skill_alignment_score=sc["skill_alignment_score"],
                        fraud_score=fr["fraud_score"],
                        fraud_risk=fr["risk_level"],
                        fraud_signals=[s["detail"] for s in fr.get("signals", [])],
                        explanation=cand_result["explanation"],
                        skill_proofs=sc.get("skill_proofs", []),
                        skill_gaps=sc.get("skill_gaps", []),
                        top_repos=gd.get("repos", [])[:4],
                        languages=gd.get("languages", {}),
                        interview_questions=cand_result.get("interview_questions", []),
                        rank=cand_result["rank"],
                        confidence=sc.get("confidence", 0.0),
                    )
                    new_db.add(candidate)
                    job_status[job_id]["progress"] = i + 1

                # Update job
                db_job = new_db.query(Job).filter(Job.id == job_id).first()
                if db_job:
                    db_job.status = "completed"
                    db_job.skills_required = result["jd_data"].get("must_have_skills", [])
                    db_job.seniority = result["jd_data"].get("seniority", "")

                new_db.commit()
                job_status[job_id]["status"] = "completed"
                job_status[job_id]["message"] = f"Analysis complete! {len(result['candidates'])} candidates ranked."
            finally:
                new_db.close()

        except Exception as e:
            job_status[job_id]["status"] = "error"
            job_status[job_id]["message"] = f"Pipeline error: {str(e)}"
            print(f"Pipeline error for job {job_id}: {e}")

    thread = threading.Thread(target=run_and_save, daemon=True)
    thread.start()

    return JobResponse(job_id=job_id, status="processing", message="Pipeline started!")


@app.get("/api/v1/jobs/{job_id}/status")
def get_job_status(job_id: str):
    """Check pipeline progress."""
    status = job_status.get(job_id, {"status": "unknown", "message": "Job not found"})
    return {"job_id": job_id, **status}


@app.get("/api/v1/jobs/{job_id}/candidates")
def get_candidates(job_id: str, db: Session = Depends(get_db)):
    """Get ranked candidates for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = db.query(Candidate).filter(
        Candidate.job_id == job_id
    ).order_by(Candidate.rank).all()

    return {
        "job_id": job_id,
        "job_title": job.title,
        "status": job.status,
        "candidates": [
            {
                "id": c.id,
                "rank": c.rank,
                "name": c.name,
                "github_username": c.github_username,
                "avatar_url": c.avatar_url,
                "bio": c.bio,
                "location": c.location,
                "public_repos": c.public_repos,
                "followers": c.followers,
                "total_score": c.total_score,
                "technical_score": c.technical_score,
                "collaboration_score": c.collaboration_score,
                "learning_velocity_score": c.learning_velocity_score,
                "code_quality_score": c.code_quality_score,
                "skill_alignment_score": c.skill_alignment_score,
                "fraud_score": c.fraud_score,
                "fraud_risk": c.fraud_risk,
                "fraud_signals": c.fraud_signals,
                "confidence": c.confidence,
                "languages": c.languages,
                "explanation": c.explanation,
                "skill_proofs": c.skill_proofs,
                "skill_gaps": c.skill_gaps,
                "top_repos": c.top_repos,
                "interview_questions": c.interview_questions,
            }
            for c in candidates
        ]
    }


@app.get("/api/v1/jobs")
def list_jobs(db: Session = Depends(get_db)):
    """List all jobs."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "status": j.status,
            "seniority": j.seniority,
            "skills": j.skills_required,
            "created_at": j.created_at.isoformat() if j.created_at else ""
        }
        for j in jobs
    ]


@app.delete("/api/v1/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and its candidates."""
    db.query(Candidate).filter(Candidate.job_id == job_id).delete()
    db.query(Job).filter(Job.id == job_id).delete()
    db.commit()
    return {"message": "Job deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
