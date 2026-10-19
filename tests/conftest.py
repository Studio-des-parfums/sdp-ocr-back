"""
Fixtures pytest partagées — bootstrappe l'app FastAPI avec tous les
services externes mockés (DB, schedulers, APIs tierces).

Stratégie : on mock get_connection() avant que les modules qui l'importent
soient chargés, puis on crée un TestClient sur l'app déjà instanciée.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Variables d'env minimales avant tout import de l'app ──────────────────
os.environ.setdefault("MISTRAL_API_KEY", "ci-dummy")
os.environ.setdefault("OPENAI_API_KEY", "ci-dummy")
os.environ.setdefault("RESEND_API_KEY", "ci-dummy")
os.environ.setdefault("RESEND_FROM_EMAIL", "no-reply@example.com")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "ci")
os.environ.setdefault("DB_PASSWORD", "ci")
os.environ.setdefault("DB_NAME", "ci_db")
os.environ.setdefault("STORAGE_BACKEND", "local")


def _make_mock_connection():
    """Retourne un mock de connexion MySQL qui ne fait rien."""
    conn = MagicMock()
    conn.open = True
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture(scope="session")
def app():
    """
    Instancie l'app FastAPI une seule fois pour toute la session de tests,
    avec DB et schedulers mockés.
    """
    mock_conn = _make_mock_connection()

    with (
        patch("app.database.get_connection", return_value=mock_conn),
        patch("app.database.connection.get_connection", return_value=mock_conn),
        patch("app.services.review_scheduler.start_review_scheduler"),
        patch("app.services.session_scheduler.start_session_scheduler"),
    ):
        from app.main import app as fastapi_app

        yield fastapi_app


@pytest.fixture(scope="session")
def client(app):
    """TestClient réutilisé pour toute la session."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
