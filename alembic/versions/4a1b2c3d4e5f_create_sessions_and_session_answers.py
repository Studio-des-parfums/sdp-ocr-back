"""create_sessions_and_session_answers

Revision ID: 4a1b2c3d4e5f
Revises: 9ec030bfd9c5
Create Date: 2026-07-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '9ec030bfd9c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(255) NULL,
            customer_email VARCHAR(255) NULL,
            status ENUM('active', 'completed', 'cancelled') NOT NULL DEFAULT 'active',
            started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS session_answers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            question_key VARCHAR(100) NOT NULL,
            answer_value JSON NOT NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            UNIQUE KEY uq_session_question (session_id, question_key)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS session_answers")
    op.execute("DROP TABLE IF EXISTS sessions")
