import uuid
from datetime import datetime
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

# Embedding dimension must match EMBEDDING_DIMENSION in settings (1536)
VECTOR_DIM = 1536


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source: Mapped[str] = mapped_column(String(50), default="manual")

    title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    domain: Mapped[str] = mapped_column(String(100), index=True)
    subdomain: Mapped[str] = mapped_column(String(100), index=True, default="")

    years_experience_min: Mapped[int] = mapped_column(Integer, default=0)
    years_experience_max: Mapped[int] = mapped_column(Integer, default=99)

    skills_required: Mapped[list] = mapped_column(JSONB, default=list)

    location: Mapped[str] = mapped_column(String(255), default="")
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    remote: Mapped[str] = mapped_column(String(20), default="onsite")
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Meaning string used to generate embedding; embedding stored for semantic search
    job_meaning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_embedding: Mapped[Optional[list]] = mapped_column(Vector(VECTOR_DIM), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
