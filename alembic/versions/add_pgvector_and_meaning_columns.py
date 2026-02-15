"""add pgvector and meaning/embedding columns

Revision ID: add_pgvector
Revises: f4aa1b3547c1
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_pgvector"
down_revision: Union[str, None] = "f4aa1b3547c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # jobs: add job_meaning, country, job_embedding; drop pinecone_id
    op.add_column("jobs", sa.Column("job_meaning", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("country", sa.String(100), nullable=True))
    op.create_index(op.f("ix_jobs_country"), "jobs", ["country"], unique=False)
    op.execute(f"ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_embedding vector({VECTOR_DIM})")
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS pinecone_id")

    # candidate_profiles: add country, summary, resume_meaning, resume_embedding
    op.add_column("candidate_profiles", sa.Column("country", sa.String(100), nullable=True))
    op.add_column("candidate_profiles", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("candidate_profiles", sa.Column("resume_meaning", sa.Text(), nullable=True))
    op.create_index(op.f("ix_candidate_profiles_country"), "candidate_profiles", ["country"], unique=False)
    op.execute(f"ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS resume_embedding vector({VECTOR_DIM})")


def downgrade() -> None:
    op.drop_index(op.f("ix_candidate_profiles_country"), table_name="candidate_profiles")
    op.execute("ALTER TABLE candidate_profiles DROP COLUMN IF EXISTS resume_embedding")
    op.drop_column("candidate_profiles", "resume_meaning")
    op.drop_column("candidate_profiles", "summary")
    op.drop_column("candidate_profiles", "country")

    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS job_embedding")
    op.drop_index(op.f("ix_jobs_country"), table_name="jobs")
    op.drop_column("jobs", "job_meaning")
    op.drop_column("jobs", "country")
    op.add_column("jobs", sa.Column("pinecone_id", sa.String(255), nullable=True))