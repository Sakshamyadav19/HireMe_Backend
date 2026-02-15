"""In-memory filter: domain, YoE band, country.

Used after vector search to narrow the candidate list.
YoE band: job range overlaps [candidate_yoe - 2, candidate_yoe + 2].
"""

from __future__ import annotations

from typing import List

from app.models.job import Job

YOE_WINDOW = 2  # ±2 years


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
