"""SQL filters: country, domain, YoE band. In-memory filter for lists.

Filter-first pipeline: filter_jobs returns all matching IDs from DB; then vector search on that set.
YoE band: job range overlaps [candidate_yoe - 2, candidate_yoe + 2].
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.job import Job

logger = logging.getLogger(__name__)

YOE_WINDOW = 2  # ±2 years


def filter_jobs(
    db: Session,
    candidate_domain: str,
    candidate_yoe: int,
    candidate_country: str | None = None,
) -> List[str]:
    """Return job IDs that pass country (if set), domain, and YoE band.

    - Country: job.country IS NULL OR job.country = candidate_country
    - Domain: exact match
    - YoE: job range overlaps [candidate_yoe - 2, candidate_yoe + 2]
    """
    delta_min = max(0, candidate_yoe - YOE_WINDOW)
    delta_max = candidate_yoe + YOE_WINDOW

    query = (
        db.query(Job.id)
        .filter(Job.domain == candidate_domain)
        .filter(Job.years_experience_min <= delta_max)
        .filter(Job.years_experience_max >= delta_min)
        .filter(Job.job_embedding.isnot(None))
    )
    if candidate_country:
        query = query.filter(
            (Job.country.is_(None)) | (Job.country == candidate_country)
        )

    rows = query.all()
    job_ids = [row[0] for row in rows]

    logger.info(
        "SQL filter: domain=%s, country=%s, yoe %d-%d → %d jobs",
        candidate_domain,
        candidate_country or "any",
        delta_min,
        delta_max,
        len(job_ids),
    )
    return job_ids


def filter_jobs_standalone(
    candidate_domain: str,
    candidate_yoe: int,
    candidate_country: str | None = None,
) -> List[str]:
    """Run filter_jobs with its own DB session. Use from a thread (e.g. parallel with embed)."""
    db = SessionLocal()
    try:
        return filter_jobs(
            db=db,
            candidate_domain=candidate_domain,
            candidate_yoe=candidate_yoe,
            candidate_country=candidate_country,
        )
    finally:
        db.close()


def filter_job_list(
    jobs: List[Job],
    candidate_domain: str,
    candidate_yoe: int,
    candidate_country: str | None = None,
) -> List[Job]:
    """Filter an in-memory list of jobs by domain, YoE band, and country.

    - Domain: exact match
    - YoE: job range overlaps [candidate_yoe - 2, candidate_yoe + 2]
    - Country: job.country is None or equals candidate_country
    """
    delta_min = max(0, candidate_yoe - YOE_WINDOW)
    delta_max = candidate_yoe + YOE_WINDOW
    out: List[Job] = []
    for j in jobs:
        if j.domain != candidate_domain:
            continue
        if j.years_experience_min > delta_max or j.years_experience_max < delta_min:
            continue
        if candidate_country and j.country is not None and j.country != candidate_country:
            continue
        out.append(j)
    return out
