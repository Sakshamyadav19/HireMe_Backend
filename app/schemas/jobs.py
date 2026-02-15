"""Pydantic schemas for job CRUD endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    title: str
    company_name: str
    description: str
    source: str
    domain: str
    subdomain: str
    years_experience_min: int
    years_experience_max: int
    skills_required: list
    location: str
    remote: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListCursorResponse(BaseModel):
    """Cursor-based list response; no total count."""

    jobs: List[JobResponse]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
