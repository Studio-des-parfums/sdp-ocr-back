"""notes_quantity_nullable

Revision ID: 9ec030bfd9c5
Revises: b335d4c2f49f
Create Date: 2026-07-22 00:56:08.236209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ec030bfd9c5'
down_revision: Union[str, Sequence[str], None] = 'b335d4c2f49f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # quantity par note est optionnelle dans le code (OCR et tablette) mais était
    # NOT NULL sans défaut en base, ce qui faisait échouer toute note sans quantité.
    op.execute("ALTER TABLE top_note MODIFY COLUMN quantity VARCHAR(255) NULL")
    op.execute("ALTER TABLE heart_note MODIFY COLUMN quantity VARCHAR(255) NULL")
    op.execute("ALTER TABLE base_note MODIFY COLUMN quantity VARCHAR(255) NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE base_note MODIFY COLUMN quantity VARCHAR(255) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE heart_note MODIFY COLUMN quantity VARCHAR(255) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE top_note MODIFY COLUMN quantity VARCHAR(255) NOT NULL DEFAULT ''")
