"""drop resumes table

Revision ID: drop_resumes_table
Revises: drop_resume_s3_url
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "drop_resumes_table"
down_revision: Union[str, None] = "drop_resume_s3_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1536


def upgrade() -> None:
    op.drop_table("resumes")


def downgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("subdomain", sa.String(100), server_default="", nullable=False),
        sa.Column("years_experience", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skills", JSONB(), server_default="[]", nullable=False),
        sa.Column("location", sa.String(255), server_default="", nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("remote_preference", sa.String(20), server_default="remote", nullable=False),
        sa.Column("resume_filename", sa.String(255), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("resume_meaning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"], unique=True)
    op.create_index(op.f("ix_resumes_domain"), "resumes", ["domain"], unique=False)
    op.create_index(op.f("ix_resumes_country"), "resumes", ["country"], unique=False)
    op.execute(f"ALTER TABLE resumes ADD COLUMN resume_embedding vector({VECTOR_DIM})")
