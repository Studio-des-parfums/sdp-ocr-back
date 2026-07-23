"""change_session_answers_value_to_text

Revision ID: d8f7e6c5b4a3
Revises: 4a1b2c3d4e5f
Create Date: 2026-07-23 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd8f7e6c5b4a3'
down_revision: Union[str, Sequence[str], None] = '4a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE session_answers MODIFY COLUMN answer_value TEXT NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE session_answers MODIFY COLUMN answer_value JSON NOT NULL")
