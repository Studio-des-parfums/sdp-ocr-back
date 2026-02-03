from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.order_schemas import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderItemCreate, OrderItemUpdate, OrderItemResponse
)
from app.repositories.order_repository import order_repository
from app.repositories.user_repository import user_repository
from app.services.email.email_sender_service import email_sender_service

router = APIRouter()


def _build_order_notification_html(user_first_name, customer_first_name, customer_last_name, order_type, order_date):
    """Construit le HTML de notification d'attribution de commande."""
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;color:#333">

<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="left" style="padding:30px">

<table width="700" cellpadding="0" cellspacing="0" style="max-width:700px">

<tr>
<td style="font-size:15px;line-height:1.6">
<p>Bonjour {user_first_name or ""},</p>
<p>Une nouvelle commande vous a été attribuée, merci de la consulter.</p>
</td>
</tr>

<tr><td height="20"></td></tr>

<tr>
<td>
<table width="100%" cellpadding="0" cellspacing="0"
       style="border:2px solid #c00000;border-radius:8px;padding:20px">
<tr>
<td style="padding:20px">
<h3 style="margin:0 0 15px;font-size:18px;color:#c00000">Informations sur la commande</h3>
<p style="margin:5px 0;font-size:14px"><strong>Client :</strong> {customer_first_name or ""} {customer_last_name or ""}</p>
<p style="margin:5px 0;font-size:14px"><strong>Type :</strong> {order_type or "Non renseigné"}</p>
<p style="margin:5px 0;font-size:14px"><strong>Date :</strong> {order_date or "Non renseignée"}</p>
</td>
</tr>
</table>
</td>
</tr>

<tr>
<td style="padding-top:30px;font-size:12px;color:#666;text-align:center">
<hr style="border:none;border-top:2px solid #333;margin-bottom:15px">
<strong>Le Studio des Parfums – Paris</strong><br>
23 rue du Bourg Tibourg – 75004 Paris<br>
Tél : +33 (0)1 40 29 90 84<br>
www.studiodesparfums-paris.fr
</td>
</tr>

</table>
</td>
</tr>
</table>

</body>
</html>
"""


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

        # Envoi de l'email de notification au responsable
        if created_order.get('responsible'):
            try:
                responsible_user = user_repository.get_user_by_id(created_order['responsible'])
                if responsible_user and responsible_user.get('email'):
                    customer = created_order.get('customer') or {}
                    html = _build_order_notification_html(
                        user_first_name=responsible_user.get('first_name'),
                        customer_first_name=customer.get('first_name'),
                        customer_last_name=customer.get('last_name'),
                        order_type=created_order.get('type'),
                        order_date=str(created_order.get('date', '')) if created_order.get('date') else None
                    )
                    email_sender_service.send_email(
                        to_email=responsible_user['email'],
                        subject="Nouvelle commande attribuée – Le Studio des Parfums",
                        body=html,
                        is_html=True
                    )
            except Exception as e:
                print(f"Erreur envoi email notification commande: {e}")

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
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    formula_id: Optional[int] = Query(None, description="Filtrer par formule"),
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    customer_name: Optional[str] = Query(None, description="Filtrer par nom du client"),
    order_type: Optional[str] = Query(None, description="Filtrer par type de commande"),
    responsible: Optional[int] = Query(None, description="Filtrer par responsable")
):
    """Récupérer toutes les commandes avec pagination et filtres"""
    try:
        orders, total = order_repository.get_all_orders(
            page=page, size=size, search=search,
            customer_id=customer_id, status=status, formula_id=formula_id,
            date_from=date_from, date_to=date_to, customer_name=customer_name,
            order_type=order_type, responsible=responsible
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

        # Envoi de l'email si le responsable a changé
        new_responsible = update_dict.get('responsible')
        if new_responsible and new_responsible != existing_order.get('responsible'):
            try:
                responsible_user = user_repository.get_user_by_id(new_responsible)
                if responsible_user and responsible_user.get('email'):
                    customer = updated_order.get('customer') or {}
                    html = _build_order_notification_html(
                        user_first_name=responsible_user.get('first_name'),
                        customer_first_name=customer.get('first_name'),
                        customer_last_name=customer.get('last_name'),
                        order_type=updated_order.get('type'),
                        order_date=str(updated_order.get('date', '')) if updated_order.get('date') else None
                    )
                    email_sender_service.send_email(
                        to_email=responsible_user['email'],
                        subject="Nouvelle commande attribuée – Le Studio des Parfums",
                        body=html,
                        is_html=True
                    )
            except Exception as e:
                print(f"Erreur envoi email notification commande: {e}")

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
