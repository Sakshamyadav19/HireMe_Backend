"""Saved jobs endpoints: add, remove, list (all require auth)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import get_current_user_id
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.schemas.jobs import JobResponse
from app.schemas.saved_jobs import SavedJobAddRequest, SavedJobListResponse

router = APIRouter(prefix="/api/saved-jobs", tags=["saved-jobs"])


@router.post("", status_code=200)
def add_saved_job(
    body: SavedJobAddRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Save a job for the current user. Returns 200 if already saved."""
    job = db.query(Job).filter(Job.id == body.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = db.query(SavedJob).filter(
        SavedJob.user_id == user_id, SavedJob.job_id == body.job_id
    ).first()
    if existing:
        return {"message": "saved"}
    db.add(SavedJob(user_id=user_id, job_id=body.job_id))
    db.commit()
    return {"message": "saved"}


@router.delete("/{job_id}", status_code=204)
def remove_saved_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove a saved job for the current user."""
    db.query(SavedJob).filter(
        SavedJob.user_id == user_id, SavedJob.job_id == job_id
    ).delete()
    db.commit()
    return None


@router.get("", response_model=SavedJobListResponse)
def list_saved_jobs(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List saved jobs for the current user (full job payloads, newest first)."""
    saved = (
        db.query(SavedJob)
        .filter(SavedJob.user_id == user_id)
        .order_by(SavedJob.created_at.desc())
        .all()
    )
    job_ids = [s.job_id for s in saved]
    if not job_ids:
        return SavedJobListResponse(jobs=[])
    jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
    job_by_id = {j.id: j for j in jobs}
    ordered = [job_by_id[jid] for jid in job_ids if jid in job_by_id]
    return SavedJobListResponse(jobs=[JobResponse.model_validate(j) for j in ordered])
