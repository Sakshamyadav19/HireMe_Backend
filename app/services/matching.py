"""Matching pipeline: SQL filter (country, domain, YoE) → pgvector top-K → rank by semantic + skill score."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.schemas.matching import MatchResponse, MatchResult
from app.services.job_filter import filter_jobs
from app.services.postgres_search import load_jobs_with_semantic_scores
from app.services.scoring import rank_jobs

logger = logging.getLogger(__name__)


@dataclass
class ResumeContext:
    """In-memory resume data for matching (no persistence)."""

    id: str
    domain: str
    years_experience: int
    country: str | None
    skills: List[str]
    resume_embedding: List[float]


async def run_matching_pipeline(
    db: Session,
    resume: ResumeContext,
    filtered_job_ids: List[str] | None = None,
) -> MatchResponse:
    """Execute the matching pipeline: SQL filter → semantic search (pgvector) → score and rank.

    If filtered_job_ids is provided (e.g. from parallel filter), the filter step is skipped.
    """
    logger.info(
        "Starting matching pipeline (domain=%s, yoe=%d, country=%s)",
        resume.domain,
        resume.years_experience,
        resume.country or "any",
    )

    resume_vec = resume.resume_embedding
    if not resume_vec:
        logger.warning("No resume_embedding; cannot run semantic search.")
        return MatchResponse(
            candidate_profile_id=resume.id,
            total_matches=0,
            matches=[],
        )
    resume_embedding_list = [float(x) for x in resume_vec]

    # A. SQL filters: country, domain, YoE band (or use precomputed IDs from parallel step)
    if filtered_job_ids is None:
        filtered_job_ids = filter_jobs(
            db=db,
            candidate_domain=resume.domain,
            candidate_yoe=resume.years_experience,
            candidate_country=resume.country,
        )

    if not filtered_job_ids:
        logger.info("No jobs passed SQL filter.")
        return MatchResponse(
            candidate_profile_id=resume.id,
            total_matches=0,
            matches=[],
        )

    # B. Semantic search: top K by cosine similarity among filtered IDs
    jobs, semantic_scores = load_jobs_with_semantic_scores(
        db=db,
        resume_embedding=resume_embedding_list,
        job_ids=filtered_job_ids,
        top_k=settings.ANN_TOP_K,
    )

    if not jobs:
        logger.info("No jobs returned from semantic search.")
        return MatchResponse(
            candidate_profile_id=resume.id,
            total_matches=0,
            matches=[],
        )

    # C. Skill check and rank
    results: List[MatchResult] = rank_jobs(
        resume_skills=resume.skills or [],
        candidate_yoe=resume.years_experience,
        jobs=jobs,
        semantic_scores=semantic_scores,
    )

    logger.info("Matching pipeline complete: %d results", len(results))
    return MatchResponse(
        candidate_profile_id=resume.id,
        total_matches=len(results),
        matches=results,
    )
