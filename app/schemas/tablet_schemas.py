from typing import List, Optional
from pydantic import BaseModel, Field


class TabletNote(BaseModel):
    """Note choisie sur la tablette (nom canonique du référentiel)"""
    name: str
    quantity: Optional[str] = None


class TabletSubmissionCreate(BaseModel):
    """Payload complet envoyé par la tablette après confirmation"""
    gender: Optional[str] = None
    first_name: str
    last_name: str
    birth_date: Optional[str] = Field(None, description="Format YYYY-MM-DD")
    job: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    phone: str
    email: str
    has_allergy: Optional[bool] = None
    liability_accepted: Optional[bool] = None
    rgpd_consent: bool
    quantity: Optional[str] = None
    perfume_name: Optional[str] = None
    top_notes: List[TabletNote] = []
    heart_notes: List[TabletNote] = []
    base_notes: List[TabletNote] = []


class TabletSubmissionResponse(BaseModel):
    """Résultat de l'enregistrement d'une soumission tablette"""
    customer_id: int
    formula_id: int
    customer_was_existing: bool
    matched_by: Optional[str] = Field(None, description="'email' ou 'phone' si client existant")


class NoteCatalogItem(BaseModel):
    """Une note du référentiel"""
    code: str
    name: str


class NotesCatalogResponse(BaseModel):
    """Référentiel des notes disponibles, groupées par type"""
    top_notes: List[NoteCatalogItem]
    heart_notes: List[NoteCatalogItem]
    base_notes: List[NoteCatalogItem]
