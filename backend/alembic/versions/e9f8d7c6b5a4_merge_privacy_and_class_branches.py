"""merge privacy and class branches

Revision ID: e9f8d7c6b5a4
Revises: 2a3b4c5d6e7f, c4d5e6f7a8b9
Create Date: 2026-08-18 00:00:00.000000
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "e9f8d7c6b5a4"
down_revision: Union[str, tuple[str, str], None] = ("2a3b4c5d6e7f", "c4d5e6f7a8b9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
