"""allow empty class creation

Revision ID: 2a3b4c5d6e7f
Revises: a9b0c1d2e3f4
Create Date: 2026-08-13 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2a3b4c5d6e7f"
down_revision: Union[str, None] = "a9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "classes",
        "teacher_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "classes",
        "teacher_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
