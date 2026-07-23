"""create_devices_table

Revision ID: a1b2c3d4e5f6
Revises: d8f7e6c5b4a3
Create Date: 2026-07-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd8f7e6c5b4a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_id VARCHAR(255) NOT NULL UNIQUE,
            device_name VARCHAR(255) NULL,
            registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen_at DATETIME NULL,
            status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
            decided_at DATETIME NULL
        )
    """)
    op.execute("""
        ALTER TABLE roles
        ADD COLUMN devices_access BOOLEAN NOT NULL DEFAULT FALSE
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE roles DROP COLUMN devices_access")
    op.execute("DROP TABLE IF EXISTS devices")
