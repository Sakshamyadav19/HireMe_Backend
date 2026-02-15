"""add resumes table (one per user), migrate from candidate_profiles, drop candidate_profiles

Revision ID: add_resumes
Revises: drop_skills_pref
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "add_resumes"
down_revision: Union[str, None] = "drop_skills_pref"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1536


def upgrade() -> None:
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
        sa.Column("resume_s3_url", sa.Text(), nullable=True),
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

    # If candidate_profiles exists (existing DB), copy active rows then drop
    conn = op.get_bind()
    has_cp = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'candidate_profiles')"
        )
    ).scalar()
    if has_cp:
        op.execute("""
            INSERT INTO resumes (
                id, user_id, domain, subdomain, years_experience, skills,
                location, country, salary_min, remote_preference,
                resume_s3_url, resume_text, summary, resume_meaning, resume_embedding,
                created_at, updated_at
            )
            SELECT
                id, user_id, domain, subdomain, years_experience, skills,
                location, country, salary_min, remote_preference,
                resume_s3_url, resume_text, summary, resume_meaning, resume_embedding,
                created_at, updated_at
            FROM candidate_profiles
            WHERE is_active = true
        """)
        op.drop_table("candidate_profiles")


def downgrade() -> None:
    op.create_table(
        "candidate_profiles",
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
        sa.Column("resume_s3_url", sa.Text(), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("resume_meaning", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_candidate_profiles_user_id"), "candidate_profiles", ["user_id"], unique=False)
    op.create_index(op.f("ix_candidate_profiles_domain"), "candidate_profiles", ["domain"], unique=False)
    op.create_index(op.f("ix_candidate_profiles_country"), "candidate_profiles", ["country"], unique=False)
    op.execute(f"ALTER TABLE candidate_profiles ADD COLUMN resume_embedding vector({VECTOR_DIM})")

    op.execute("""
        INSERT INTO candidate_profiles (
            id, user_id, domain, subdomain, years_experience, skills,
            location, country, salary_min, remote_preference,
            resume_s3_url, resume_text, summary, resume_meaning, resume_embedding,
            is_active, created_at, updated_at
        )
        SELECT
            id, user_id, domain, subdomain, years_experience, skills,
            location, country, salary_min, remote_preference,
            resume_s3_url, resume_text, summary, resume_meaning, resume_embedding,
            true, created_at, updated_at
        FROM resumes
    """)

    op.drop_table("resumes")
