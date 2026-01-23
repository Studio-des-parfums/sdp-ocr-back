from pydantic import BaseModel
from typing import Optional


class RoleBase(BaseModel):
    """Schéma de base pour les rôles"""
    name: str
    csv: int = 0
    pdf: int = 0
    email_sending: bool = False
    customer_validation: bool = False


class RoleCreate(RoleBase):
    """Schéma pour la création d'un rôle"""
    pass


class RoleUpdate(BaseModel):
    """Schéma pour la mise à jour d'un rôle"""
    name: Optional[str] = None
    csv: Optional[int] = None
    pdf: Optional[int] = None
    email_sending: Optional[bool] = None
    customer_validation: Optional[bool] = None


class RoleResponse(RoleBase):
    """Schéma de réponse pour un rôle"""
    id: int

    class Config:
        from_attributes = True
