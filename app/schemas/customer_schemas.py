from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class NoteSchema(BaseModel):
    """
    Schéma pour une note (tête / cœur / fond) d'une formule
    """
    id: int
    name: str
    quantity: Optional[str] = None


class FormulaWithNotes(BaseModel):
    """
    Schéma pour une formule avec ses notes associées
    """
    id: int
    customer_id: Optional[int] = None
    file_id: int
    reference: Optional[str] = None
    perfume_name: Optional[str] = None
    top_notes: List[NoteSchema] = []
    heart_notes: List[NoteSchema] = []
    base_notes: List[NoteSchema] = []


class CustomerBase(BaseModel):
    """Schema de base pour les customers"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    job: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    date: Optional[str] = None
    verified_email: Optional[bool] = None
    verified_domain: Optional[bool] = None
    verified_phone: Optional[bool] = None

class CustomerCreate(CustomerBase):
    """Schema pour créer un customer"""
    pass

class CustomerUpdate(CustomerBase):
    """Schema pour modifier un customer"""
    pass

class CustomerResponse(CustomerBase):
    """Schema de réponse avec l'ID"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    verified_email: Optional[bool] = None
    verified_domain: Optional[bool] = None
    verified_phone: Optional[bool] = None
    formulas: List[FormulaWithNotes] = []

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
    customers: List[CustomerBulkUpdateItem]


class CustomerBulkUpdateResultItem(BaseModel):
    """Schema pour le résultat d'un item de mise à jour en masse"""
    id: int
    success: bool
    error: Optional[str] = None


class CustomerBulkUpdateResponse(BaseModel):
    """Schema pour la réponse de mise à jour en masse"""
    updated: List[CustomerBulkUpdateResultItem]
    total_requested: int
    total_updated: int