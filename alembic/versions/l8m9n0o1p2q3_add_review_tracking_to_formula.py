"""add_review_tracking_to_formula

Revision ID: l8m9n0o1p2q3
Revises: k7l8m9n0o1p2
Create Date: 2026-10-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'l8m9n0o1p2q3'
down_revision: Union[str, Sequence[str], None] = 'k7l8m9n0o1p2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE formula ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
    op.execute("ALTER TABLE formula ADD COLUMN review_email_sent_at TIMESTAMP NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE formula DROP COLUMN review_email_sent_at")
    op.execute("ALTER TABLE formula DROP COLUMN created_at")
