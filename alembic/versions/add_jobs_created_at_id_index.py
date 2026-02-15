"""add index on jobs (created_at DESC, id) for cursor pagination

Revision ID: add_jobs_created_at_id_idx
Revises: drop_resumes_table
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op

revision: str = "add_jobs_created_at_id_idx"
down_revision: Union[str, None] = "drop_resumes_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_jobs_created_at_id",
        "jobs",
        ["created_at", "id"],
        unique=False,
        postgresql_ops={"created_at": "DESC", "id": "DESC"},
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_created_at_id", table_name="jobs")
