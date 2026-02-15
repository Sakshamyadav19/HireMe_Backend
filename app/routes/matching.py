"""Resume upload + job matching endpoint.

POST /api/match/upload     — Enqueue match job, return 202 with job_id.
GET  /api/match/status/{id} — Job status (pending | processing | completed | failed).
GET  /api/match/results    — Cursor-paginated read of latest match results (auth required). Returns empty list if none.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import get_current_user_id
from app.models.match_job import MatchJob
from app.schemas.matching import MatchJobAccepted, MatchJobStatus, MatchResultsCursorResponse
from app.services.match_result_cache import get_match_results_page
from app.services.match_job_queue import enqueue_match_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/match", tags=["matching"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=MatchJobAccepted, status_code=202)
async def upload_and_match(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upload a resume and enqueue a background match job. Returns 202 with job_id; poll GET /status/{job_id}."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB).")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Allowed types: PDF, DOCX, TXT.")

    job_id = uuid.uuid4().hex
    enqueue_match_job(db, job_id, user_id, file_bytes, file.filename or "resume")
    return MatchJobAccepted(job_id=job_id)


@router.get("/status/{job_id}", response_model=MatchJobStatus)
def get_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return status of a match job. 404 if not found or not owned by current user."""
    row = db.query(MatchJob).filter(MatchJob.id == job_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found.")
    if row.user_id != user_id:
        raise HTTPException(status_code=404, detail="Job not found.")
    return MatchJobStatus(job_id=row.id, status=row.status, error=row.error)


@router.get("/results", response_model=MatchResultsCursorResponse)
def get_results(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    dir: str = Query("next"),
):
    """Return one page of the user's latest match results (cursor-based). Returns empty list if none."""
    if dir not in ("next", "prev"):
        raise HTTPException(status_code=400, detail="dir must be 'next' or 'prev'")
    if dir == "prev" and not cursor:
        raise HTTPException(status_code=400, detail="cursor required for dir=prev")
    page = get_match_results_page(db, user_id, cursor=cursor, limit=limit, dir=dir)
    if page is None:
        return MatchResultsCursorResponse(
            total_matches=0,
            matches=[],
            next_cursor=None,
            prev_cursor=None,
        )
    return page
