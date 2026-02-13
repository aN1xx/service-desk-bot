"""Initial tables

Revision ID: 001
Revises:
Create Date: 2026-01-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "owners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(20), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("residential_complex", sa.String(50), nullable=False),
        sa.Column("block", sa.String(10), nullable=True),
        sa.Column("entrance", sa.String(10), nullable=True),
        sa.Column("apartment", sa.String(20), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, index=True, nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "masters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("residential_complex", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.String(30), unique=True, index=True, nullable=False),
        sa.Column("client_telegram_id", sa.BigInteger(), index=True, nullable=False),
        sa.Column("client_phone", sa.String(20), nullable=False),
        sa.Column("client_full_name", sa.String(255), nullable=False),
        sa.Column("residential_complex", sa.String(50), index=True, nullable=False),
        sa.Column("category", sa.String(50), index=True, nullable=False),
        sa.Column("sub_category", sa.String(255), nullable=True),
        sa.Column("block", sa.String(10), nullable=True),
        sa.Column("entrance", sa.String(10), nullable=True),
        sa.Column("apartment", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("face_id_photos", sa.JSON(), nullable=True),
        sa.Column("car_plate", sa.String(20), nullable=True),
        sa.Column("car_gate", sa.String(100), nullable=True),
        sa.Column("parking_number", sa.String(20), nullable=True),
        sa.Column("camera_access_email", sa.String(255), nullable=True),
        sa.Column("camera_access_details", sa.Text(), nullable=True),
        sa.Column("key_count", sa.Integer(), nullable=True),
        sa.Column("key_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), index=True, nullable=False, server_default="new"),
        sa.Column("assigned_master_id", sa.Integer(), sa.ForeignKey("masters.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("rating_comment", sa.Text(), nullable=True),
        sa.Column("rated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ticket_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), index=True, nullable=False),
        sa.Column("old_status", sa.String(30), nullable=True),
        sa.Column("new_status", sa.String(30), nullable=False),
        sa.Column("changed_by_id", sa.BigInteger(), nullable=True),
        sa.Column("changed_by_role", sa.String(20), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_history")
    op.drop_table("tickets")
    op.drop_table("admins")
    op.drop_table("masters")
    op.drop_table("owners")
