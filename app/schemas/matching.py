"""Pydantic schemas for matching pipeline responses."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    skills: float = Field(..., description="Skills overlap score 0-100")
    semantic: float = Field(..., description="Semantic similarity score 0-100")
    yoe: float = Field(..., description="YoE fit score 0-100")


class MatchExplanation(BaseModel):
    matched_skills: List[str] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    summary: str = Field("", description="Human-readable explanation")


class JobSummary(BaseModel):
    id: str
    title: str
    company_name: str
    domain: str
    subdomain: str
    location: str
    remote: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    skills_required: List[str] = Field(default_factory=list)
    years_experience_min: int = 0
    years_experience_max: int = 99

    model_config = {"from_attributes": True}


class MatchResult(BaseModel):
    job: JobSummary
    score: float = Field(..., description="Composite score 0-100")
    breakdown: ScoreBreakdown
    explanation: MatchExplanation


class MatchResponse(BaseModel):
    """Top-level response for the matching endpoint."""
    candidate_profile_id: str
    total_matches: int
    matches: List[MatchResult]


class MatchResultsCursorResponse(BaseModel):
    """Cursor-paginated match results (upload first page or GET /results)."""
    total_matches: int
    matches: List[MatchResult] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None


class MatchJobAccepted(BaseModel):
    """202 response: job accepted for background processing."""
    job_id: str


class MatchJobStatus(BaseModel):
    """Status of a match job (GET /match/status/{job_id})."""
    job_id: str
    status: str  # pending | processing | completed | failed
    error: Optional[str] = None
