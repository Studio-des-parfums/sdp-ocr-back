from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from enum import Enum
from datetime import datetime


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
    name: Optional[str] = None
    quantity: Optional[int] = None


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
    comment: Optional[str] = None
    allergy: Optional[str] = None
    type: Optional[str] = None
    responsible: Optional[int] = None


class OrderCreate(OrderBase):
    """Schéma pour la création d'une commande"""
    items: Optional[List[OrderItemCreate]] = None


class OrderUpdate(BaseModel):
    """Schéma pour la mise à jour d'une commande"""
    customer_id: Optional[int] = None
    formula_id: Optional[int] = None
    comment: Optional[str] = None
    allergy: Optional[str] = None
    status: Optional[OrderStatus] = None
    type: Optional[str] = None
    responsible: Optional[int] = None


class OrderResponse(OrderBase):
    """Schéma de réponse pour une commande"""
    id: int
    status: OrderStatus
    date: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    customer: Optional[Dict[str, Any]] = None
    formula: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
