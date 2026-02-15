"""Job read-only endpoints.

Job ingestion is done only via the seed script with a JSON file (scripts/seed_jobs.py --file jobs.json).

GET  /api/jobs         — List jobs (cursor-based, next/prev)
GET  /api/jobs/{id}    — Get a single job
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.job import Job
from app.schemas.jobs import JobListCursorResponse, JobResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _encode_cursor(created_at: datetime, job_id: str) -> str:
    """Cursor format: created_at_iso,job_id (created_at has no comma in ISO format)."""
    return f"{created_at.isoformat()},{job_id}"


def _decode_cursor(cursor: str) -> tuple[datetime, str] | None:
    """Parse cursor into (created_at, job_id). Returns None if invalid."""
    if not cursor or "," not in cursor:
        return None
    parts = cursor.split(",", 1)
    try:
        created_at = datetime.fromisoformat(parts[0].replace("Z", "+00:00"))
        job_id = parts[1].strip()
        return (created_at, job_id) if job_id else None
    except (ValueError, IndexError):
        return None


@router.get("", response_model=JobListCursorResponse)
async def list_jobs(
    cursor: str | None = Query(None),
    dir: str = Query("next"),
    limit: int = Query(50, ge=1, le=100),
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List jobs with cursor-based pagination (next/prev). No total count."""
    query = db.query(Job)
    if domain:
        query = query.filter(Job.domain == domain)

    if dir == "prev":
        if not cursor:
            raise HTTPException(status_code=400, detail="cursor required for dir=prev")
        decoded = _decode_cursor(cursor)
        if not decoded:
            raise HTTPException(status_code=400, detail="Invalid cursor")
        created_at, job_id = decoded
        query = (
            query.filter(
                (Job.created_at > created_at) | ((Job.created_at == created_at) & (Job.id > job_id))
            )
            .order_by(Job.created_at.asc(), Job.id.asc())
            .limit(limit)
        )
        jobs = query.all()
        jobs = list(reversed(jobs))
    else:
        if cursor:
            decoded = _decode_cursor(cursor)
            if not decoded:
                raise HTTPException(status_code=400, detail="Invalid cursor")
            created_at, job_id = decoded
            query = query.filter(
                (Job.created_at < created_at) | ((Job.created_at == created_at) & (Job.id < job_id))
            )
        query = query.order_by(Job.created_at.desc(), Job.id.desc()).limit(limit)
        jobs = query.all()

    out = [JobResponse.model_validate(j) for j in jobs]
    next_cursor = _encode_cursor(jobs[-1].created_at, jobs[-1].id) if jobs else None
    prev_cursor = _encode_cursor(jobs[0].created_at, jobs[0].id) if jobs else None

    return JobListCursorResponse(
        jobs=out,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get a single job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobResponse.model_validate(job)
