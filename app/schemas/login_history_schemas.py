from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LoginHistoryCreate(BaseModel):
    """
    Schéma pour créer un enregistrement d'historique de connexion
    """

    user_id: int
    type: Literal["connexion", "deconnexion"]


class LoginHistoryResponse(BaseModel):
    """
    Schéma de réponse pour un enregistrement d'historique de connexion
    """

    id: int
    user_id: int
    ip_address: str
    city: str
    country: str
    type: str
    logged_at: datetime
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class LoginHistoryListResponse(BaseModel):
    """
    Schéma de réponse pour la liste paginée d'historique de connexions
    """

    records: list[LoginHistoryResponse]
    total: int
    page: int
    size: int
    total_pages: int
