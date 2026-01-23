from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.role_schemas import RoleCreate, RoleUpdate, RoleResponse
from app.repositories.role_repository import role_repository

router = APIRouter()


@router.post("/", response_model=RoleResponse)
async def create_role(role_data: RoleCreate):
    """Créer un nouveau rôle"""
    try:
        role_dict = role_data.model_dump()
        role_id = role_repository.create_role(role_dict)

        if role_id is None:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la création du rôle")

        created_role = role_repository.get_role_by_id(role_id)
        if created_role is None:
            raise HTTPException(status_code=500,
                                detail="Rôle créé mais impossible de le récupérer")

        return created_role
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la création du rôle: {str(e)}")


@router.get("/", response_model=dict)
async def get_roles(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(10, ge=1, le=100, description="Taille de la page"),
    search: Optional[str] = Query(None, description="Terme de recherche")
):
    """Récupérer tous les rôles avec pagination"""
    try:
        roles, total = role_repository.get_all_roles(
            page=page, size=size, search=search
        )

        return {
            "roles": roles,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if total > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la récupération des rôles: {str(e)}")


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int):
    """Récupérer un rôle par son ID"""
    try:
        role = role_repository.get_role_by_id(role_id)
        if role is None:
            raise HTTPException(status_code=404, detail="Rôle non trouvé")
        return role
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la récupération du rôle: {str(e)}")


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role_data: RoleUpdate):
    """Mettre à jour un rôle"""
    try:
        existing_role = role_repository.get_role_by_id(role_id)
        if existing_role is None:
            raise HTTPException(status_code=404, detail="Rôle non trouvé")

        update_dict = role_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400,
                                detail="Aucune donnée à mettre à jour")

        success = role_repository.update_role(role_id, update_dict)
        if not success:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la mise à jour du rôle")

        updated_role = role_repository.get_role_by_id(role_id)
        return updated_role
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la mise à jour du rôle: {str(e)}")


@router.delete("/{role_id}")
async def delete_role(role_id: int):
    """Supprimer un rôle définitivement"""
    try:
        existing_role = role_repository.get_role_by_id(role_id)
        if existing_role is None:
            raise HTTPException(status_code=404, detail="Rôle non trouvé")

        success = role_repository.delete_role(role_id)
        if not success:
            raise HTTPException(status_code=500,
                                detail="Erreur lors de la suppression du rôle")
        return {"message": f"Rôle {role_id} supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de la suppression du rôle: {str(e)}")
