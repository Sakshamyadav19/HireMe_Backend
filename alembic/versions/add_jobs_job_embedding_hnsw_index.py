"""add HNSW index on jobs.job_embedding for fast approximate nearest neighbor search

Revision ID: add_job_embedding_hnsw
Revises: add_match_jobs
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op

revision: str = "add_job_embedding_hnsw"
down_revision: Union[str, None] = "add_match_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector: HNSW index for cosine distance (<=> operator)
    op.execute(
        "CREATE INDEX ix_jobs_job_embedding_hnsw ON jobs "
        "USING hnsw (job_embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_jobs_job_embedding_hnsw")
