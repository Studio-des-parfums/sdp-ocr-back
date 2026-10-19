from pydantic import BaseModel


class RoleBase(BaseModel):
    """Schéma de base pour les rôles"""

    name: str
    csv_download_limit: int = 0
    email_sending: bool = False
    pdf_extraction_limit: int = 0
    customers_access: bool = False
    customers_edit: bool = False
    access_to_extraction: bool = False
    customers_review_access: bool = False
    formula_edit: bool = False
    full_access: bool = False
    devices_access: bool = False


class RoleCreate(RoleBase):
    """Schéma pour la création d'un rôle"""

    pass


class RoleUpdate(BaseModel):
    """Schéma pour la mise à jour d'un rôle"""

    name: str | None = None
    csv_download_limit: int | None = None
    email_sending: bool | None = None
    pdf_extraction_limit: int | None = None
    customers_access: bool | None = None
    customers_edit: bool | None = None
    access_to_extraction: bool | None = None
    customers_review_access: bool | None = None
    formula_edit: bool | None = None
    full_access: bool | None = None
    devices_access: bool | None = None


class RoleResponse(RoleBase):
    """Schéma de réponse pour un rôle"""

    id: int
    csv_download_limit: int | None = 0
    pdf_extraction_limit: int | None = 0

    class Config:
        from_attributes = True
