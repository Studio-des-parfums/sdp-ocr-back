from pydantic import BaseModel, EmailStr
from typing import Optional


class EmailSendRequest(BaseModel):
    """Schema pour envoyer un email"""
    to_email: EmailStr
    subject: str
    body: str
    is_html: Optional[bool] = False


class EmailTestRequest(BaseModel):
    """Schema pour envoyer un email de test"""
    to_email: EmailStr


class EmailResponse(BaseModel):
    """Schema de reponse pour l'envoi d'email"""
    success: bool
    message: str
