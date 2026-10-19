from datetime import datetime

from pydantic import BaseModel, field_validator


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


class CustomerReviewBase(BaseModel):
    """
    Schéma de base pour les customers review
    """

    last_name: str | None = None
    first_name: str | None = None
    phone: str | None = None
    email: str | None = None
    job: str | None = None
    country: str | None = None
    city: str | None = None
    date: str | None = None
    verified_email: str | None = None
    verified_domain: str | None = None
    verified_phone: str | None = None
    type: str
    v2: bool = False


class CustomerReviewCreate(CustomerReviewBase):
    """
    Schéma pour créer un customer review
    """

    pass


class CustomerReviewUpdate(BaseModel):
    """
    Schéma pour mettre à jour un customer review
    """

    last_name: str | None = None
    first_name: str | None = None
    phone: str | None = None
    email: str | None = None
    job: str | None = None
    country: str | None = None
    city: str | None = None
    date: str | None = None
    verified_email: str | None = None
    verified_domain: str | None = None
    verified_phone: str | None = None
    type: str | None = None


class CustomerReviewResponse(CustomerReviewBase):
    """
    Schéma de réponse pour un customer review
    """

    id: int
    created_at: datetime | None = None
    formulas: list[FormulaWithNotes] = []

    @field_validator("verified_email", "verified_domain", "verified_phone", mode="before")
    @classmethod
    def validate_verified_email(cls, v):
        """Convertit les valeurs non-string en string pour verified_email, verified_domain et verified_phone"""
        if v is None:
            return None
        return str(v) if v not in [0, ""] else None

    @field_validator(
        "email", "phone", "job", "city", "country", "date", "first_name", "last_name", mode="before"
    )
    @classmethod
    def validate_string_fields(cls, v):
        """Convertit les valeurs non-string en string et traite les valeurs vides"""
        if v is None or v == "" or v == 0:
            return None
        return str(v)

    class Config:
        from_attributes = True


class CustomerReviewListResponse(BaseModel):
    """
    Schéma de réponse pour la liste paginée de customers review
    """

    customers: list[CustomerReviewResponse]
    total: int
    page: int
    size: int
    total_pages: int


class TransferResponse(BaseModel):
    """
    Schéma de réponse pour le transfert d'un customer review vers customers
    """

    success: bool
    message: str
    customer_id: int | None = None
    review_id: int
