"""In-memory queue + background worker for match jobs. Status stored in DB (match_jobs)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.match_job import MatchJob
from app.schemas.matching import MatchResponse
from app.services.embedding import embed_text
from app.services.job_filter import filter_jobs_standalone
from app.services.match_result_cache import save_match_results
from app.services.matching import ResumeContext, run_matching_pipeline
from app.services.reducto_parser import build_resume_meaning, parse_resume_with_reducto

logger = logging.getLogger(__name__)

# In-memory queue: (job_id, user_id, file_bytes, filename)
_match_queue: asyncio.Queue[tuple[str, str, bytes, str]] = asyncio.Queue()


def enqueue_match_job(
    db: Session,
    job_id: str,
    user_id: str,
    file_bytes: bytes,
    filename: str,
) -> None:
    """Insert status row and put work item on the in-memory queue. Call from async route (same thread as loop)."""
    row = MatchJob(
        id=job_id,
        user_id=user_id,
        status="pending",
        error=None,
    )
    db.add(row)
    db.commit()
    _match_queue.put_nowait((job_id, user_id, file_bytes, filename))


def _set_job_status(db: Session, job_id: str, status: str, error: str | None = None) -> None:
    row = db.query(MatchJob).filter(MatchJob.id == job_id).first()
    if row:
        row.status = status
        row.error = error
        db.commit()


async def _run_one_job(job_id: str, user_id: str, file_bytes: bytes, filename: str) -> None:
    """Parse, embed, match, save; update match_jobs status. Uses its own DB session."""
    db = SessionLocal()
    try:
        _set_job_status(db, job_id, "processing")

        resume_data = await asyncio.to_thread(
            parse_resume_with_reducto, file_bytes, filename
        )
        resume_meaning = build_resume_meaning(
            domain=resume_data["domain"],
            yoe=resume_data["yoe"],
            skills=resume_data["skills"],
            summary=resume_data["summary"],
        )
        # Run embed and SQL filter in parallel to overlap I/O
        raw_embedding, filtered_job_ids = await asyncio.gather(
            embed_text(resume_meaning),
            asyncio.to_thread(
                filter_jobs_standalone,
                resume_data["domain"],
                resume_data["yoe"],
                resume_data.get("country"),
            ),
        )
        resume_embedding = [float(x) for x in raw_embedding]

        resume_ctx = ResumeContext(
            id="ephemeral",
            domain=resume_data["domain"],
            years_experience=resume_data["yoe"],
            country=resume_data.get("country") or None,
            skills=resume_data["skills"] or [],
            resume_embedding=resume_embedding,
        )
        response: MatchResponse = await run_matching_pipeline(
            db, resume_ctx, filtered_job_ids=filtered_job_ids
        )
        save_match_results(db, user_id, response.total_matches, response.matches)
        _set_job_status(db, job_id, "completed")
        logger.info("Match job %s completed: %d matches", job_id, response.total_matches)
    except Exception as e:
        logger.exception("Match job %s failed", job_id)
        _set_job_status(db, job_id, "failed", error=str(e))
    finally:
        db.close()


async def _worker_loop() -> None:
    """Long-lived task: pull from queue and run the matching pipeline."""
    logger.info("Match job worker started.")
    while True:
        try:
            job_id, user_id, file_bytes, filename = await _match_queue.get()
            await _run_one_job(job_id, user_id, file_bytes, filename)
        except asyncio.CancelledError:
            logger.info("Match job worker cancelled.")
            break
        except Exception as e:
            logger.exception("Worker loop error: %s", e)


def get_match_queue() -> asyncio.Queue[tuple[str, str, bytes, str]]:
    """Return the in-memory queue (for enqueue from route)."""
    return _match_queue


def start_match_worker() -> asyncio.Task[Any]:
    """Start the background worker task. Call from app startup."""
    return asyncio.create_task(_worker_loop())
