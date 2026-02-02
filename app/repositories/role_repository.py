from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_role


class RoleRepository:
    """Repository pour la gestion des rôles"""

    def create_role(self, role_data: Dict[str, Any]) -> Optional[int]:
        """Créer un nouveau rôle"""
        connection = get_connection()
        if not connection:
            return None
        try:
            role_id = crud_role.create(connection, role_data)
            if role_id:
                print(f"Rôle créé avec ID: {role_id}")
            return role_id
        finally:
            connection.close()

    def get_role_by_id(self, role_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un rôle par son ID"""
        connection = get_connection()
        if not connection:
            return None
        try:
            return crud_role.get_by_id(connection, role_id)
        finally:
            connection.close()

    def get_all_roles(self, page: int = 1, size: int = 10,
                      search: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Récupérer tous les rôles avec pagination"""
        connection = get_connection()
        if not connection:
            return [], 0
        try:
            return crud_role.get_all(connection, page, size, search)
        finally:
            connection.close()

    def update_role(self, role_id: int, role_data: Dict[str, Any]) -> bool:
        """Mettre à jour un rôle"""
        connection = get_connection()
        if not connection:
            return False
        try:
            success = crud_role.update(connection, role_id, role_data)
            if success:
                print(f"Rôle {role_id} mis à jour")
            else:
                print(f"Rôle {role_id} non trouvé")
            return success
        finally:
            connection.close()

    def delete_role(self, role_id: int) -> bool:
        """Supprimer un rôle définitivement"""
        connection = get_connection()
        if not connection:
            return False
        try:
            success = crud_role.delete(connection, role_id)
            if success:
                print(f"Rôle {role_id} supprimé")
            return success
        finally:
            connection.close()


role_repository = RoleRepository()
