"""add saved_jobs table

Revision ID: add_saved_jobs
Revises: add_jobs_created_at_id_idx
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_saved_jobs"
down_revision: Union[str, None] = "add_jobs_created_at_id_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_jobs",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "job_id"),
    )
    op.create_index(op.f("ix_saved_jobs_user_id"), "saved_jobs", ["user_id"], unique=False)
    op.create_index(op.f("ix_saved_jobs_job_id"), "saved_jobs", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_saved_jobs_job_id"), table_name="saved_jobs")
    op.drop_index(op.f("ix_saved_jobs_user_id"), table_name="saved_jobs")
    op.drop_table("saved_jobs")
