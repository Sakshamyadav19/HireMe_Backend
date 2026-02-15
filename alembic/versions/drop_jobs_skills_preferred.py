"""drop jobs.skills_preferred

Revision ID: drop_skills_pref
Revises: add_pgvector
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "drop_skills_pref"
down_revision: Union[str, None] = "add_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS skills_preferred")


def downgrade() -> None:
    op.add_column("jobs", sa.Column("skills_preferred", JSONB(), server_default="[]", nullable=False))
