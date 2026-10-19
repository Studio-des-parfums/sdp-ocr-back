from datetime import datetime

from pydantic import BaseModel

from app.schemas.role_schemas import RoleResponse


class UserBase(BaseModel):
    """Schema de base pour les users"""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    job: str | None = None
    role_id: int | None = None
    is_online: bool | None = False
    team: str | None = None
    identifier: str | None = None
    csv_download_count: int | None = 0
    csv_download_reset_at: datetime | None = None
    pdf_extraction_count: int | None = 0
    pdf_extraction_reset_at: datetime | None = None


class UserCreate(UserBase):
    """Schema pour créer un user"""

    pass


class UserUpdate(UserBase):
    """Schema pour modifier un user"""

    pass


class UserResponse(UserBase):
    """Schema de réponse avec l'ID"""

    id: int
    identifier: str | None = None
    last_login_at: datetime | None = None
    csv_download_count: int | None = 0
    csv_download_reset_at: datetime | None = None
    pdf_extraction_count: int | None = 0
    pdf_extraction_reset_at: datetime | None = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema pour la liste des users"""

    users: list[UserResponse]
    total: int
    page: int
    size: int


class UserLoginUpdate(BaseModel):
    """Schema pour mettre à jour le statut de connexion"""

    is_online: bool
    last_login_at: datetime | None = None


class UserWithRoleResponse(BaseModel):
    """Schema de réponse avec les infos utilisateur et son rôle complet"""

    id: int
    identifier: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    job: str | None = None
    is_online: bool | None = False
    team: str | None = None
    last_login_at: datetime | None = None
    csv_download_count: int | None = 0
    csv_download_reset_at: datetime | None = None
    pdf_extraction_count: int | None = 0
    pdf_extraction_reset_at: datetime | None = None
    role: RoleResponse | None = None

    class Config:
        from_attributes = True
