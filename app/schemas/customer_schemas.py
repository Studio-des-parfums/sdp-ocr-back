from datetime import datetime

from pydantic import BaseModel


class NoteSchema(BaseModel):
    """
    Schéma pour une note (tête / cœur / fond) d'une formule
    """

    id: int
    name: str
    quantity: str | None = None


class FormulaWithNotes(BaseModel):
    """
    Schéma pour une formule avec ses notes associées
    """

    id: int
    customer_id: int | None = None
    file_id: int | None = None
    reference: str | None = None
    perfume_name: str | None = None
    top_notes: list[NoteSchema] = []
    heart_notes: list[NoteSchema] = []
    base_notes: list[NoteSchema] = []


class CustomerBase(BaseModel):
    """Schema de base pour les customers"""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    job: str | None = None
    city: str | None = None
    country: str | None = None
    date: str | None = None
    verified_email: bool | None = None
    verified_domain: bool | None = None
    verified_phone: bool | None = None


class CustomerCreate(CustomerBase):
    """Schema pour créer un customer"""

    pass


class CustomerUpdate(CustomerBase):
    """Schema pour modifier un customer"""

    pass


class CustomerResponse(CustomerBase):
    """Schema de réponse avec l'ID"""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    verified_email: bool | None = None
    verified_domain: bool | None = None
    verified_phone: bool | None = None
    formulas: list[FormulaWithNotes] = []

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Schema pour la liste des customers"""

    customers: list[CustomerResponse]
    total: int
    page: int
    size: int


class CustomerBulkUpdateItem(CustomerBase):
    """Schema pour un item de mise à jour en masse"""

    id: int


class CustomerBulkUpdateRequest(BaseModel):
    """Schema pour la requête de mise à jour en masse"""

    customers: list[CustomerBulkUpdateItem]


class CustomerBulkUpdateResultItem(BaseModel):
    """Schema pour le résultat d'un item de mise à jour en masse"""

    id: int
    success: bool
    error: str | None = None


class CustomerBulkUpdateResponse(BaseModel):
    """Schema pour la réponse de mise à jour en masse"""

    updated: list[CustomerBulkUpdateResultItem]
    total_requested: int
    total_updated: int
