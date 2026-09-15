"""add_atelier_to_formula

Revision ID: k7l8m9n0o1p2
Revises: j6k7l8m9n0o1
Create Date: 2026-09-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'k7l8m9n0o1p2'
down_revision: Union[str, Sequence[str], None] = 'j6k7l8m9n0o1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    atelier_id_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'atelier_id'")
    ).scalar()
    if not atelier_id_exists:
        op.execute("ALTER TABLE formula ADD COLUMN atelier_id INT NULL")

    atelier_name_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'atelier_name'")
    ).scalar()
    if not atelier_name_exists:
        op.execute("ALTER TABLE formula ADD COLUMN atelier_name VARCHAR(255) NULL")


def downgrade() -> None:
    connection = op.get_bind()

    atelier_id_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'atelier_id'")
    ).scalar()
    if atelier_id_exists:
        op.execute("ALTER TABLE formula DROP COLUMN atelier_id")

    atelier_name_exists = connection.execute(
        text("SELECT COUNT(*) FROM information_schema.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'formula' AND COLUMN_NAME = 'atelier_name'")
    ).scalar()
    if atelier_name_exists:
        op.execute("ALTER TABLE formula DROP COLUMN atelier_name")
