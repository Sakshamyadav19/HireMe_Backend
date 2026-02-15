"""drop resume_s3_url from resumes

Revision ID: drop_resume_s3_url
Revises: add_resume_filename
Create Date: 2026-02-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "drop_resume_s3_url"
down_revision: Union[str, None] = "add_resume_filename"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("resumes", "resume_s3_url")


def downgrade() -> None:
    op.add_column("resumes", sa.Column("resume_s3_url", sa.Text(), nullable=True))
