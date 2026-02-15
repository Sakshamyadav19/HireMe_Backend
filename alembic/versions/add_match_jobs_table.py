"""add match_jobs table

Revision ID: add_match_jobs
Revises: add_match_result_cache
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_match_jobs"
down_revision: Union[str, None] = "add_match_result_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_jobs",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_jobs_user_id"), "match_jobs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_match_jobs_user_id"), table_name="match_jobs")
    op.drop_table("match_jobs")
