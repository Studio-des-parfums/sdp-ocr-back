"""create_formula_option_table

Revision ID: q3r4s5t6u7v8
Revises: p2q3r4s5t6u7
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'q3r4s5t6u7v8'
down_revision: Union[str, Sequence[str], None] = 'p2q3r4s5t6u7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Options choisies pour une formule (ex: Ruban, Champagne, Flacon murano). Le référentiel
    # d'options vit dans la base MySQL du dashboard (hôte/port différents), donc pas de FK SQL
    # possible vers lui — on stocke le nom (même principe que top_note/heart_note/base_note/
    # booster_note pour les notes, ou atelier_name pour l'atelier).
    op.execute("""
        CREATE TABLE IF NOT EXISTS formula_option (
            id INT AUTO_INCREMENT PRIMARY KEY,
            formula_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            FOREIGN KEY (formula_id) REFERENCES formula(id) ON DELETE CASCADE
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS formula_option")
