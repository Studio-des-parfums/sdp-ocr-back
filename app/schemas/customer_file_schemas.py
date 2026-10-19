from datetime import datetime

from pydantic import BaseModel


class CustomerFileBase(BaseModel):
    """Schema de base pour les fichiers customers"""

    customer_id: int | None = None
    customer_review_id: int | None = None
    file_path: str
    file_name: str
    file_type: str
    file_size: int


class CustomerFileCreate(CustomerFileBase):
    """Schema pour créer un fichier customer"""

    pass


class CustomerFileUpdate(BaseModel):
    """Schema pour mettre à jour un fichier customer"""

    customer_id: int | None = None
    customer_review_id: int | None = None
    file_path: str | None = None
    file_name: str | None = None


class CustomerFileResponse(CustomerFileBase):
    """Schema de réponse avec l'ID et timestamps"""

    id: int
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CustomerFileListResponse(BaseModel):
    """Schema pour la liste des fichiers d'un customer"""

    files: list[CustomerFileResponse]
    total: int
