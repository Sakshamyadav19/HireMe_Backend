"""add match_result_cache table

Revision ID: add_match_result_cache
Revises: add_saved_jobs
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "add_match_result_cache"
down_revision: Union[str, None] = "add_saved_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_result_cache",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("total_matches", sa.Integer(), nullable=False),
        sa.Column("matches_json", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("match_result_cache")
