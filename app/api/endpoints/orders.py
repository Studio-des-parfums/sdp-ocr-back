from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.order_schemas import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderItemCreate, OrderItemUpdate, OrderItemResponse
)
from app.repositories.order_repository import order_repository

router = APIRouter()


# ==================== ORDERS ====================

@router.post("/", response_model=OrderResponse)
async def create_order(order_data: OrderCreate):
    """Créer une nouvelle commande"""
    try:
        order_dict = order_data.model_dump()
        # Convertir les items en liste de dicts
        if order_dict.get('items'):
            order_dict['items'] = [item for item in order_dict['items']]

        order_id = order_repository.create_order(order_dict)

        if order_id is None:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la création de la commande")

        created_order = order_repository.get_order_by_id(order_id)
        if created_order is None:
            raise HTTPException(status_code=500,
                                detail="Commande créée mais impossible de la récupérer")

        return created_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la création de la commande: {str(e)}")


@router.get("/", response_model=dict)
async def get_orders(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de la page"),
    search: Optional[str] = Query(None, description="Recherche dans les commentaires"),
    customer_id: Optional[int] = Query(None, description="Filtrer par client"),
    status: Optional[str] = Query(None, description="Filtrer par statut")
):
    """Récupérer toutes les commandes avec pagination"""
    try:
        orders, total = order_repository.get_all_orders(
            page=page, size=size, search=search,
            customer_id=customer_id, status=status
        )

        return {
            "orders": orders,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if total > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la récupération des commandes: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int):
    """Récupérer une commande par son ID"""
    try:
        order = order_repository.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la récupération de la commande: {str(e)}")


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, order_data: OrderUpdate):
    """Mettre à jour une commande"""
    try:
        existing_order = order_repository.get_order_by_id(order_id)
        if existing_order is None:
            raise HTTPException(status_code=404, detail="Commande non trouvée")

        update_dict = order_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400,
                                detail="Aucune donnée à mettre à jour")

        success = order_repository.update_order(order_id, update_dict)
        if not success:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la mise à jour de la commande")

        updated_order = order_repository.get_order_by_id(order_id)
        return updated_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la mise à jour de la commande: {str(e)}")


@router.delete("/{order_id}")
async def delete_order(order_id: int):
    """Supprimer une commande"""
    try:
        existing_order = order_repository.get_order_by_id(order_id)
        if existing_order is None:
            raise HTTPException(status_code=404, detail="Commande non trouvée")

        success = order_repository.delete_order(order_id)
        if not success:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la suppression de la commande")
        return {"message": f"Commande {order_id} supprimée avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la suppression de la commande: {str(e)}")


# ==================== ORDER ITEMS ====================

@router.post("/{order_id}/items", response_model=OrderItemResponse)
async def add_item_to_order(order_id: int, item_data: OrderItemCreate):
    """Ajouter un item à une commande"""
    try:
        # Vérifier que la commande existe
        existing_order = order_repository.get_order_by_id(order_id)
        if existing_order is None:
            raise HTTPException(status_code=404, detail="Commande non trouvée")

        item_dict = item_data.model_dump()
        item_id = order_repository.add_item_to_order(order_id, item_dict)

        if item_id is None:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de l'ajout de l'item")

        created_item = order_repository.get_order_item_by_id(item_id)
        if created_item is None:
            raise HTTPException(status_code=500,
                                detail="Item créé mais impossible de le récupérer")

        return created_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de l'ajout de l'item: {str(e)}")


@router.put("/{order_id}/items/{item_id}", response_model=OrderItemResponse)
async def update_order_item(order_id: int, item_id: int, item_data: OrderItemUpdate):
    """Mettre à jour un item de commande"""
    try:
        # Vérifier que l'item existe et appartient à la commande
        existing_item = order_repository.get_order_item_by_id(item_id)
        if existing_item is None:
            raise HTTPException(status_code=404, detail="Item non trouvé")
        if existing_item['order_id'] != order_id:
            raise HTTPException(status_code=400,
                                detail="L'item n'appartient pas à cette commande")

        update_dict = item_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400,
                                detail="Aucune donnée à mettre à jour")

        success = order_repository.update_order_item(item_id, update_dict)
        if not success:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la mise à jour de l'item")

        updated_item = order_repository.get_order_item_by_id(item_id)
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la mise à jour de l'item: {str(e)}")


@router.delete("/{order_id}/items/{item_id}")
async def delete_order_item(order_id: int, item_id: int):
    """Supprimer un item de commande"""
    try:
        # Vérifier que l'item existe et appartient à la commande
        existing_item = order_repository.get_order_item_by_id(item_id)
        if existing_item is None:
            raise HTTPException(status_code=404, detail="Item non trouvé")
        if existing_item['order_id'] != order_id:
            raise HTTPException(status_code=400,
                                detail="L'item n'appartient pas à cette commande")

        success = order_repository.delete_order_item(item_id)
        if not success:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la suppression de l'item")
        return {"message": f"Item {item_id} supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la suppression de l'item: {str(e)}")
