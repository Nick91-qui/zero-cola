"""add omr template owner

Revision ID: e6f7a8b9c0d1
Revises: d1e2f3a4b5c6
Create Date: 2026-07-29 09:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "omr_templates",
        sa.Column("created_by", sa.UUID(), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE omr_templates
            SET created_by = exams.teacher_id
            FROM exams
            WHERE omr_templates.exam_id = exams.id
              AND omr_templates.created_by IS NULL
            """
        )
    )
    op.create_foreign_key(
        "fk_omr_templates_created_by_users",
        "omr_templates",
        "users",
        ["created_by"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_omr_templates_created_by_users",
        "omr_templates",
        type_="foreignkey",
    )
    op.drop_column("omr_templates", "created_by")
