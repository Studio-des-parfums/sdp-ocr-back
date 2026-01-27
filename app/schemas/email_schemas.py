from pydantic import BaseModel, EmailStr


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
