"""create_ocr_jobs_table

Revision ID: n0o1p2q3r4s5
Revises: m9n0o1p2q3r4
Create Date: 2026-10-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'n0o1p2q3r4s5'
down_revision: Union[str, Sequence[str], None] = 'm9n0o1p2q3r4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE ocr_jobs (
            id VARCHAR(36) PRIMARY KEY,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            progress INT NOT NULL DEFAULT 0,
            total_pages INT NOT NULL DEFAULT 0,
            filename VARCHAR(255) NULL,
            result JSON NULL,
            error TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_ocr_jobs_created_at (created_at)
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE ocr_jobs")
