"""refactor attempts to answer_key references

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-28 09:00:00.000000

Step 2 — Attempt References.

This migration is additive and keeps the legacy OMR grading flow intact.
It adds the new Attempt/AttemptAnswer reference columns and backfills
existing rows from the already-materialized AnswerKey layer.

The Step 3 code switch is intentionally NOT part of this migration.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from app.services.backfill import backfill_attempt_references

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "attempts",
        sa.Column("answer_key_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "attempts",
        sa.Column(
            "attempt_number",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "attempts",
        sa.Column(
            "source",
            sa.String(length=10),
            nullable=False,
            server_default="OMR",
        ),
    )
    op.add_column(
        "attempt_answers",
        sa.Column("answer_key_item_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "attempt_answers",
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column(
        "attempts",
        "status",
        existing_type=sa.String(length=20),
        server_default="not_started",
        existing_nullable=False,
    )

    backfill_attempt_references(op.get_bind())


def downgrade() -> None:
    op.alter_column(
        "attempts",
        "status",
        existing_type=sa.String(length=20),
        server_default="graded",
        existing_nullable=False,
    )

    op.drop_column("attempt_answers", "answered_at")
    op.drop_column("attempt_answers", "answer_key_item_id")
    op.drop_column("attempts", "source")
    op.drop_column("attempts", "attempt_number")
    op.drop_column("attempts", "answer_key_id")
