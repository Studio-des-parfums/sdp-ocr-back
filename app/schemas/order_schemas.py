from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class OrderStatus(str, Enum):
    """Statuts possibles pour une commande"""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ==================== ORDER ITEMS ====================


class OrderItemBase(BaseModel):
    """Schéma de base pour les items de commande"""

    name: str
    quantity: int


class OrderItemCreate(OrderItemBase):
    """Schéma pour la création d'un item de commande"""

    pass


class OrderItemUpdate(BaseModel):
    """Schéma pour la mise à jour d'un item de commande"""

    name: str | None = None
    quantity: int | None = None


class OrderItemResponse(OrderItemBase):
    """Schéma de réponse pour un item de commande"""

    id: int
    order_id: int

    class Config:
        from_attributes = True


# ==================== ORDERS ====================


class OrderBase(BaseModel):
    """Schéma de base pour les commandes"""

    customer_id: int
    formula_id: int
    comment: str | None = None
    allergy: str | None = None
    type: str | None = None
    responsible: int | None = None
    desired_date: str | None = None


class OrderCreate(OrderBase):
    """Schéma pour la création d'une commande"""

    items: list[OrderItemCreate] | None = None


class OrderUpdate(BaseModel):
    """Schéma pour la mise à jour d'une commande"""

    customer_id: int | None = None
    formula_id: int | None = None
    comment: str | None = None
    allergy: str | None = None
    status: OrderStatus | None = None
    type: str | None = None
    responsible: int | None = None
    desired_date: str | None = None


class OrderResponse(OrderBase):
    """Schéma de réponse pour une commande"""

    id: int
    reference: str | None = None
    status: OrderStatus
    date: datetime | None = None
    desired_date: datetime | None = None
    items: list[OrderItemResponse] = []
    customer: dict[str, Any] | None = None
    formula: dict[str, Any] | None = None

    class Config:
        from_attributes = True
