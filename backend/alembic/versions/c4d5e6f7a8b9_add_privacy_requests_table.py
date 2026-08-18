"""add privacy requests table

Revision ID: c4d5e6f7a8b9
Revises: f7a8b9c0d1e2
Create Date: 2026-08-18 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "privacy_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("requested_by_id", sa.UUID(), nullable=True),
        sa.Column("request_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_privacy_requests_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_id"],
            ["users.id"],
            name="fk_privacy_requests_requested_by_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_id"],
            ["users.id"],
            name="fk_privacy_requests_reviewed_by_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_privacy_requests_user_id", "privacy_requests", ["user_id"])
    op.create_index("ix_privacy_requests_status", "privacy_requests", ["status"])
    op.create_index("ix_privacy_requests_type", "privacy_requests", ["request_type"])
    op.create_index("ix_privacy_requests_created_at", "privacy_requests", ["created_at"])
    op.create_index(
        "ix_privacy_requests_pending_user_type",
        "privacy_requests",
        ["user_id", "request_type"],
        unique=True,
        sqlite_where=sa.text("status = 'pending'"),
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("ix_privacy_requests_pending_user_type", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_created_at", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_type", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_status", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_user_id", table_name="privacy_requests")
    op.drop_table("privacy_requests")
