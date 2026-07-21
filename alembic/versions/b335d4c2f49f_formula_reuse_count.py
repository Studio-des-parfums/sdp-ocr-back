"""formula_reuse_count

Revision ID: b335d4c2f49f
Revises: 49089947c1cf
Create Date: 2026-07-22 00:12:58.895207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b335d4c2f49f'
down_revision: Union[str, Sequence[str], None] = '49089947c1cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE formula ADD COLUMN reuse_count INT NOT NULL DEFAULT 0")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE formula DROP COLUMN reuse_count")
