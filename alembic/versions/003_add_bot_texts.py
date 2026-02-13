"""Add bot_texts table for configurable messages

Revision ID: 003
Revises: 002
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bot_texts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bot_texts_key", "bot_texts", ["key"], unique=True)

    # Insert default texts
    op.execute("""
        INSERT INTO bot_texts (key, value, description) VALUES
        ('welcome', 'Добро пожаловать в сервисную службу <b>Qvartal Smart Security</b>!

Для начала работы, пожалуйста, отправьте ваш контакт для авторизации.', 'Welcome message before auth'),
        ('auth_success', 'Авторизация успешна! Добро пожаловать, <b>{full_name}</b>.', 'Auth success message'),
        ('auth_failed', 'Вы не найдены в базе собственников.
Обратитесь в сервисную службу для регистрации.', 'Auth failed message'),
        ('ticket_created', 'Заявка <b>№{ticket_id}</b> принята. Статус: <b>Новая</b>

Мы уведомим вас об изменениях статуса.', 'Ticket created confirmation'),
        ('ticket_car_plate_pending', 'Заявка <b>№{ticket_id}</b> принята.
Статус: <b>На рассмотрении</b>

Ваша заявка будет рассмотрена мастером и администратором. Мы уведомим вас о решении.', 'Car plate ticket created message')
    """)


def downgrade() -> None:
    op.drop_index("ix_bot_texts_key", table_name="bot_texts")
    op.drop_table("bot_texts")
