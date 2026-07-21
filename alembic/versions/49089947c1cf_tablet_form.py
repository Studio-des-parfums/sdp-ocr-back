"""tablet_form

Revision ID: 49089947c1cf
Revises: 
Create Date: 2026-07-22 00:12:24.380373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49089947c1cf'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Les formules tablette n'ont pas de fiche scannée
    op.execute("ALTER TABLE formula MODIFY COLUMN file_id INT NULL")

    # 2) Traçabilité et quantité choisie sur la formule
    op.execute("ALTER TABLE formula ADD COLUMN quantity VARCHAR(20) NULL")
    op.execute("ALTER TABLE formula ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'ocr'")

    # 3) Champs collectés par le questionnaire tablette absents de customers
    op.execute("ALTER TABLE customers ADD COLUMN gender VARCHAR(10) NULL")
    op.execute("ALTER TABLE customers ADD COLUMN birth_date DATE NULL")
    op.execute("ALTER TABLE customers ADD COLUMN has_allergy TINYINT(1) NULL")
    op.execute("ALTER TABLE customers ADD COLUMN liability_accepted TINYINT(1) NULL")
    op.execute("ALTER TABLE customers ADD COLUMN rgpd_consent TINYINT(1) NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE customers DROP COLUMN rgpd_consent")
    op.execute("ALTER TABLE customers DROP COLUMN liability_accepted")
    op.execute("ALTER TABLE customers DROP COLUMN has_allergy")
    op.execute("ALTER TABLE customers DROP COLUMN birth_date")
    op.execute("ALTER TABLE customers DROP COLUMN gender")
    op.execute("ALTER TABLE formula DROP COLUMN source")
    op.execute("ALTER TABLE formula DROP COLUMN quantity")
    op.execute("ALTER TABLE formula MODIFY COLUMN file_id INT NOT NULL")
