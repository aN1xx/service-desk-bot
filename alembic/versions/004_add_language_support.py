"""Add language support to bot_texts and user tables

Revision ID: 004
Revises: 003
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- bot_texts: add language column ---
    op.add_column("bot_texts", sa.Column("language", sa.String(2), server_default="ru", nullable=False))

    # Drop old unique index on key alone
    op.drop_index("ix_bot_texts_key", table_name="bot_texts")

    # Create new unique index on (key, language)
    op.create_index("ix_bot_texts_key_language", "bot_texts", ["key", "language"], unique=True)

    # --- user tables: add language preference ---
    op.add_column("owners", sa.Column("language", sa.String(2), server_default="ru", nullable=False))
    op.add_column("masters", sa.Column("language", sa.String(2), server_default="ru", nullable=False))
    op.add_column("admins", sa.Column("language", sa.String(2), server_default="ru", nullable=False))


def downgrade() -> None:
    op.drop_column("admins", "language")
    op.drop_column("masters", "language")
    op.drop_column("owners", "language")

    op.drop_index("ix_bot_texts_key_language", table_name="bot_texts")
    op.create_index("ix_bot_texts_key", "bot_texts", ["key"], unique=True)
    op.drop_column("bot_texts", "language")
