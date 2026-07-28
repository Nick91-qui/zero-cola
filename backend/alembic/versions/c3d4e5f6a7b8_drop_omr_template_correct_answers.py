"""drop legacy omr template correct_answers

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-28 10:00:00.000000

Step 4 — Remove Legacy OMR Answer Key Storage.

This migration drops the legacy `omr_templates.correct_answers` JSON column
now that AnswerKey/AnswerKeyItem are the canonical answer-key source.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("omr_templates", "correct_answers")


def downgrade() -> None:
    op.add_column(
        "omr_templates",
        sa.Column("correct_answers", sa.JSON(), nullable=True),
    )
