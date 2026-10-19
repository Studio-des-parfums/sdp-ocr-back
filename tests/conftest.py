"""
Fixtures pytest partagées pour tous les tests.

Les tests unitaires ne doivent pas nécessiter une vraie DB ou des APIs externes.
Ce fichier met en place les mocks nécessaires pour que l'app FastAPI puisse être
importée et testée en CI sans aucun service externe.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Assure que les variables d'env minimales sont définies avant tout import
# ──────────────────────────────────────────────────────────────────────────────
os.environ.setdefault("MISTRAL_API_KEY", "ci-dummy")
os.environ.setdefault("OPENAI_API_KEY", "ci-dummy")
os.environ.setdefault("RESEND_API_KEY", "ci-dummy")
os.environ.setdefault("RESEND_FROM_EMAIL", "no-reply@example.com")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "ci")
os.environ.setdefault("DB_PASSWORD", "ci")
os.environ.setdefault("DB_NAME", "ci_db")
os.environ.setdefault("STORAGE_BACKEND", "local")


@pytest.fixture(autouse=True, scope="session")
def mock_db_connection():
    """Mock la connexion DB pour tous les tests : évite toute tentative de
    connexion réelle à MySQL."""
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    with patch("app.database.get_connection", return_value=mock_conn):
        yield mock_conn


@pytest.fixture(autouse=True, scope="session")
def mock_schedulers():
    """Mock les schedulers APScheduler pour ne pas démarrer de threads en CI."""
    with (
        patch("app.services.review_scheduler.start_review_scheduler"),
        patch("app.services.session_scheduler.start_session_scheduler"),
    ):
        yield
