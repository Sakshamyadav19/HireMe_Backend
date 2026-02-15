#!/usr/bin/env python3
"""Seed jobs from a JSON file into the database.

Job ingestion is only supported from a JSON file. Each job gets job_meaning (text) and
job_embedding (vector) stored in Postgres. Usage (from backend/, venv activated):

    python -m scripts.seed_jobs --file jobs.json

The JSON file must be an array of job objects with at least: title, company_name.
Optional: description, source, domain, subdomain, years_experience_min/max,
skills_required, location, country, remote, salary_min, salary_max.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.database import Base, SessionLocal, engine
from app.models.job import Job
from app.services.embedding import build_job_meaning, embed_text


def job_dict_to_model(data: dict) -> Job:
    """Build a Job model from a seed dict (no id; job_meaning/job_embedding set separately)."""
    yoe_min = data.get("years_experience_min", 0)
    yoe_max = data.get("years_experience_max")
    if yoe_max is None:
        yoe_max = yoe_min + 2
    return Job(
        source=data.get("source", "script"),
        title=data["title"],
        company_name=data.get("company_name", ""),
        description=data.get("description", ""),
        domain=data.get("domain", "Engineering"),
        subdomain=data.get("subdomain", ""),
        years_experience_min=yoe_min,
        years_experience_max=yoe_max,
        skills_required=data.get("skills_required") or [],
        location=data.get("location", ""),
        country=data.get("country"),
        remote=data.get("remote", "onsite"),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
    )


async def embed_and_save_jobs(db: Session, jobs: list[Job]) -> int:
    """Build job_meaning, embed, and update each job in DB. Returns count of successes."""
    success = 0
    for job in jobs:
        try:
            job_meaning = build_job_meaning(
                title=job.title,
                domain=job.domain,
                subdomain=job.subdomain or "",
                years_experience_min=job.years_experience_min,
                skills_required=job.skills_required or [],
                description=job.description or "",
            )
            vector = await embed_text(job_meaning)
            job.job_meaning = job_meaning
            job.job_embedding = vector
            db.commit()
            success += 1
        except Exception as e:
            print(f"  ✗ Embed failed for {job.id}: {e}")
    return success


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed jobs from a JSON file into the database (with embeddings in Postgres)."
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to JSON file with job definitions (array of job objects)",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        print("JSON file must be an array of job objects.")
        sys.exit(1)
    jobs_data = raw

    # Ensure DB has pgvector and tables (idempotent; safe if already applied)
    print("Ensuring database extension and tables exist...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    print("Done.\n")

    print(f"Seeding {len(jobs_data)} jobs into the database...\n")

    db: Session = SessionLocal()
    try:
        created: list[Job] = []
        for i, data in enumerate(jobs_data, 1):
            job = job_dict_to_model(data)
            db.add(job)
            db.commit()
            db.refresh(job)
            created.append(job)
            print(f"[{i}/{len(jobs_data)}] Inserted: {job.title} at {job.company_name} (id={job.id})")

        if created:
            print("\nBuilding embeddings and saving to Postgres...")
            n = asyncio.run(embed_and_save_jobs(db, created))
            print(f"  ✓ Embedded and saved {n}/{len(created)} jobs.")
    finally:
        db.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
