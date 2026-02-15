"""add resume_filename to resumes

Revision ID: add_resume_filename
Revises: add_resumes
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "add_resume_filename"
down_revision: Union[str, None] = "add_resumes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("resume_filename", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "resume_filename")
