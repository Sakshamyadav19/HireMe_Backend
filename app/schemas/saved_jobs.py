"""Pydantic schemas for saved-jobs endpoints."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.schemas.jobs import JobResponse


class SavedJobAddRequest(BaseModel):
    job_id: str = Field(..., min_length=1)


class SavedJobListResponse(BaseModel):
    jobs: List[JobResponse]
