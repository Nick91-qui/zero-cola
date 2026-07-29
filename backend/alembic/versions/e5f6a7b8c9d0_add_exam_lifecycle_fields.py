"""add exam lifecycle fields

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-29 11:00:00.000000

Step 7 — Exam Lifecycle.

Adds the exam lifecycle status used by the approved target domain model.
Existing exams are marked as published because they are already in use.
New exams default to draft.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exams",
        sa.Column("status", sa.String(length=20), nullable=True),
    )
    op.execute(sa.text("UPDATE exams SET status = 'published'"))
    op.alter_column(
        "exams",
        "status",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default="draft",
    )
    op.create_check_constraint(
        "ck_exams_status_valid",
        "exams",
        "status IN ('draft', 'published', 'archived')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_exams_status_valid",
        "exams",
        type_="check",
    )
    op.drop_column("exams", "status")
