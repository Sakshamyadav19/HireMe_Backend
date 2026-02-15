"""add users, jobs and candidate_profiles tables

Revision ID: f4aa1b3547c1
Revises:
Create Date: 2026-02-14 12:34:23.537934

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f4aa1b3547c1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users (referenced by candidate_profiles)
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # jobs (add_pgvector will add job_meaning, country, job_embedding and drop pinecone_id)
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source", sa.String(50), server_default="manual", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), server_default="", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("subdomain", sa.String(100), server_default="", nullable=False),
        sa.Column("years_experience_min", sa.Integer(), server_default="0", nullable=False),
        sa.Column("years_experience_max", sa.Integer(), server_default="99", nullable=False),
        sa.Column("skills_required", JSONB(), server_default="[]", nullable=False),
        sa.Column("location", sa.String(255), server_default="", nullable=False),
        sa.Column("remote", sa.String(20), server_default="onsite", nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("pinecone_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_jobs_domain"), "jobs", ["domain"], unique=False)
    op.create_index(op.f("ix_jobs_subdomain"), "jobs", ["subdomain"], unique=False)

    # candidate_profiles (add_pgvector will add country, summary, resume_meaning, resume_embedding)
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("subdomain", sa.String(100), server_default="", nullable=False),
        sa.Column("years_experience", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skills", JSONB(), server_default="[]", nullable=False),
        sa.Column("location", sa.String(255), server_default="", nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("remote_preference", sa.String(20), server_default="remote", nullable=False),
        sa.Column("resume_s3_url", sa.Text(), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_candidate_profiles_user_id"), "candidate_profiles", ["user_id"], unique=False)
    op.create_index(op.f("ix_candidate_profiles_domain"), "candidate_profiles", ["domain"], unique=False)


def downgrade() -> None:
    op.drop_table("candidate_profiles")
    op.drop_table("jobs")
    op.drop_table("users")
