"""add online attempt engine fields

Revision ID: d1e2f3a4b5c6
Revises: e5f6a7b8c9d0
Create Date: 2026-07-29 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exams",
        sa.Column("total_time_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "exams",
        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.add_column(
        "exams",
        sa.Column(
            "randomization_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_check_constraint(
        "ck_attempts_status_valid",
        "attempts",
        "status IN ('not_started', 'in_progress', 'submitted', 'graded')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_attempts_status_valid", "attempts", type_="check")
    op.drop_column("exams", "randomization_enabled")
    op.drop_column("exams", "max_attempts")
    op.drop_column("exams", "total_time_seconds")
