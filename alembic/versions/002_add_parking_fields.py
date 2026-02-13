"""Add parking fields for car plate approval flow

Revision ID: 002
Revises: 001
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("has_parking", sa.Boolean(), nullable=True))
    op.add_column("tickets", sa.Column("parking_reason", sa.Text(), nullable=True))
    op.add_column("tickets", sa.Column("parking_contract_photo", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "parking_contract_photo")
    op.drop_column("tickets", "parking_reason")
    op.drop_column("tickets", "has_parking")
