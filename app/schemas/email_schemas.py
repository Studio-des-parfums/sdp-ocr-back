from pydantic import BaseModel, EmailStr
from typing import Optional


class EmailTestRequest(BaseModel):
    """Schema pour envoyer un email de test"""
    to_email: EmailStr


class PyramidRequest(BaseModel):
    """Schema pour la route pyramid"""
    reference: str


class EmailResponse(BaseModel):
    """Schema de reponse pour l'envoi d'email"""
    success: bool
    message: str


class PyramidPreviewResponse(BaseModel):
    """Schema de reponse pour le preview de la pyramide"""
    subject: str
    html: str
    to_email: Optional[str] = None
    customer_name: Optional[str] = None
