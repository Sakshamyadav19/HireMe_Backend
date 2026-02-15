"""Scoring: skills overlap (denominator = job required only), YoE fit, composite, explanation."""

from __future__ import annotations

import logging
from typing import Dict, List, Set, Tuple

from app.config.settings import settings
from app.models.job import Job
from app.schemas.matching import MatchExplanation, MatchResult, ScoreBreakdown, JobSummary

logger = logging.getLogger(__name__)


def _normalise_skill(s: str) -> str:
    """Normalise skill for comparison (lowercase, stripped)."""
    return s.strip().lower() if s else ""


def _canonicalise(skills: list) -> Set[str]:
    """Normalise a list of skill strings to a set of lowercase forms for comparison."""
    return {_normalise_skill(s) for s in skills if s}


def skills_score_required_only(
    resume_skills: List[str],
    job_required: List[str],
) -> Tuple[float, Set[str], Set[str]]:
    """Score = fraction of job required skills the candidate has. Denominator = job required only.

    Returns (score_0_100, matched_skills_display, missing_required).
    """
    r_set = _canonicalise(resume_skills)
    req_canon = _canonicalise(job_required)
    matched_req = r_set & req_canon
    missing_req = req_canon - r_set
    total_required = len(req_canon)
    if total_required == 0:
        return (0.0, set(), set())
    score = (len(matched_req) / total_required) * 100.0
    req_map = {_normalise_skill(s): s for s in job_required if s}
    matched_display = {req_map.get(s, s) for s in matched_req}
    missing_display = {req_map.get(s, s) for s in missing_req}
    return (min(score, 100.0), matched_display, missing_display)


def yoe_fit_score(candidate_yoe: int, job_min: int, job_max: int) -> float:
    """Compute YoE fit as 0-100.

    100 = candidate is at the centre of the job's range.
    Linearly decays toward the edges of the ±window.
    """
    window = settings.YOE_WINDOW
    job_centre = (job_min + job_max) / 2.0
    distance = abs(candidate_yoe - job_centre)
    max_distance = window + (job_max - job_min) / 2.0

    if max_distance == 0:
        return 100.0

    fit = max(0.0, 1.0 - distance / max_distance) * 100.0
    return min(fit, 100.0)


def composite_score(
    skills_score: float,
    semantic_score: float,
    yoe_score: float,
) -> float:
    """Weighted sum: skills 45%, semantic 40%, YoE 15%."""
    return (
        settings.WEIGHT_SKILLS * skills_score
        + settings.WEIGHT_SEMANTIC * semantic_score
        + settings.WEIGHT_YOE * yoe_score
    )


def rank_jobs(
    resume_skills: List[str],
    candidate_yoe: int,
    jobs: List[Job],
    semantic_scores: Dict[str, float],
) -> List[MatchResult]:
    """Score and rank a list of jobs against a candidate's profile.

    Args:
        resume_skills: Candidate's canonical skills.
        candidate_yoe: Candidate's years of experience.
        jobs: Job ORM objects (already filtered by domain + YoE).
        semantic_scores: {job_id: cosine_similarity_0_1} from Pinecone.

    Returns:
        Sorted list of MatchResult (highest composite score first).
    """
    logger.info(
        "[scoring] rank_jobs start: jobs=%d, candidate_yoe=%d, resume_skills_count=%d",
        len(jobs),
        candidate_yoe,
        len(resume_skills or []),
    )
    results: List[MatchResult] = []

    for job in jobs:
        job_req = job.skills_required or []
        skills_raw, matched, missing_req = skills_score_required_only(
            resume_skills,
            job_req,
        )

        sem_01 = semantic_scores.get(job.id, 0.0)
        sem_raw = sem_01 * 100.0
        yoe_raw = yoe_fit_score(candidate_yoe, job.years_experience_min, job.years_experience_max)
        comp = 0.5 * sem_raw + 0.5 * skills_raw

        total_required = len(job_req)
        matched_count = total_required - len(missing_req) if total_required else 0

        logger.info(
            "[scoring] job=%s | company=%s | skills: %d/%d -> %.1f | semantic: %.4f -> %.1f | yoe: %.1f | composite: 0.5*%.1f + 0.5*%.1f = %.1f",
            job.title,
            job.company_name,
            matched_count,
            total_required,
            skills_raw,
            sem_01,
            sem_raw,
            yoe_raw,
            skills_raw,
            sem_raw,
            comp,
        )

        summary = ""
        if total_required > 0:
            summary = f"You match {matched_count} of {total_required} required skills."
            if missing_req:
                summary += f" Missing: {', '.join(sorted(missing_req))}."
        else:
            summary = f"Matched {len(matched)} skills." if matched else "No required skills listed."

        results.append(
            MatchResult(
                job=JobSummary.model_validate(job),
                score=round(comp, 1),
                breakdown=ScoreBreakdown(
                    skills=round(skills_raw, 1),
                    semantic=round(sem_raw, 1),
                    yoe=round(yoe_raw, 1),
                ),
                explanation=MatchExplanation(
                    matched_skills=sorted(matched),
                    missing_required=sorted(missing_req),
                    summary=summary,
                ),
            )
        )

    # Sort by composite score, descending
    results.sort(key=lambda r: r.score, reverse=True)
    if results:
        top = [(r.job.title, r.job.company_name, r.score) for r in results[:5]]
        logger.info("[scoring] rank_jobs done. top 5: %s", top)
    return results
