from typing import Dict, Any, Optional, List, Tuple
from app.database import get_connection
from app.crud import crud_group
from app.services.group import group_business_service


class GroupRepository:
    """
    Repository pour gérer l'accès aux données groupes (Data Access Layer)
    """

    def create_group(self, group_data: Dict[str, Any]) -> Optional[int]:
        """
        Crée un nouveau groupe

        Args:
            group_data: Dictionnaire contenant name, description, created_by

        Returns:
            ID du groupe créé ou None si erreur
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            group_id = crud_group.create(connection, group_data)
            if group_id:
                print(f"Groupe créé avec ID: {group_id}")
            return group_id
        finally:
            connection.close()

    def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un groupe par son ID (seulement les non supprimés)

        Args:
            group_id: ID du groupe

        Returns:
            Dictionnaire avec les données du groupe ou None
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_group.get_by_id(connection, group_id, include_deleted=False)
        finally:
            connection.close()

    def get_all_groups(self, page: int = 1, size: int = 10, search: Optional[str] = None,
                      include_deleted: bool = False) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les groupes avec pagination et recherche

        Args:
            page: Numéro de page
            size: Taille de page
            search: Terme de recherche
            include_deleted: Inclure les groupes supprimés

        Returns:
            Tuple (liste des groupes, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            return crud_group.get_all(connection, page, size, search, include_deleted)
        finally:
            connection.close()

    def update_group(self, group_id: int, group_data: Dict[str, Any]) -> bool:
        """
        Met à jour un groupe

        Args:
            group_id: ID du groupe
            group_data: Nouvelles données (name, description)

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_group.update(connection, group_id, group_data)

            if success:
                print(f"Groupe {group_id} mis à jour")
            else:
                print(f"Groupe {group_id} non trouvé ou déjà supprimé")

            return success
        finally:
            connection.close()

    def soft_delete_group(self, group_id: int) -> bool:
        """
        Suppression logique d'un groupe (is_deleted = TRUE)

        Args:
            group_id: ID du groupe

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_group.soft_delete(connection, group_id)

            if success:
                print(f"Groupe {group_id} supprimé (soft delete)")
            else:
                print(f"Groupe {group_id} non trouvé ou déjà supprimé")

            return success
        finally:
            connection.close()

    def restore_group(self, group_id: int) -> bool:
        """
        Restaure un groupe supprimé (is_deleted = FALSE)

        Args:
            group_id: ID du groupe

        Returns:
            True si succès, False sinon
        """
        connection = get_connection()
        if not connection:
            return False

        try:
            success = crud_group.restore(connection, group_id)

            if success:
                print(f"Groupe {group_id} restauré")
            else:
                print(f"Groupe {group_id} non trouvé ou pas supprimé")

            return success
        finally:
            connection.close()

    # ======================================================================
    # CUSTOMER-GROUP RELATIONS
    # ======================================================================

    def add_customers_to_group(self, group_id: int, customer_ids: List[int],
                              added_by: int) -> Dict[str, Any]:
        """
        Ajoute plusieurs customers à un groupe
        Délègue à group_business_service

        Args:
            group_id: ID du groupe
            customer_ids: Liste des IDs des customers
            added_by: ID de l'utilisateur qui ajoute

        Returns:
            Dict avec succès/échecs détaillés
        """
        return group_business_service.add_customers_to_group(group_id, customer_ids, added_by)

    def remove_customers_from_group(self, group_id: int, customer_ids: List[int]) -> Dict[str, Any]:
        """
        Retire plusieurs customers d'un groupe
        Délègue à group_business_service

        Args:
            group_id: ID du groupe
            customer_ids: Liste des IDs des customers

        Returns:
            Dict avec succès/échecs détaillés
        """
        return group_business_service.remove_customers_from_group(group_id, customer_ids)

    def get_group_customers(self, group_ids: List[int], page: int = 1,
                           size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Récupère tous les customers d'un ou plusieurs groupes avec pagination

        Args:
            group_ids: Liste des IDs des groupes
            page: Numéro de page
            size: Taille de page

        Returns:
            Tuple (liste des customers, total)
        """
        connection = get_connection()
        if not connection:
            return [], 0

        try:
            return crud_group.get_group_customers(connection, group_ids, page, size)
        finally:
            connection.close()

    def get_customer_groups(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Récupère tous les groupes d'un customer

        Args:
            customer_id: ID du customer

        Returns:
            Liste des groupes
        """
        connection = get_connection()
        if not connection:
            return []

        try:
            return crud_group.get_customer_groups(connection, customer_id)
        finally:
            connection.close()

    def merge_groups(self, source_group_ids: List[int], new_group_name: str,
                    description: Optional[str], created_by: int) -> Dict[str, Any]:
        """
        Fusionne plusieurs groupes en créant un nouveau groupe avec tous les customers uniques

        Args:
            source_group_ids: Liste des IDs des groupes à fusionner
            new_group_name: Nom du nouveau groupe
            description: Description du nouveau groupe
            created_by: ID de l'utilisateur créant le merge

        Returns:
            Dict avec le nouveau groupe et les statistiques
        """
        connection = get_connection()
        if not connection:
            return {
                "success": False,
                "message": "Erreur de connexion à la base de données"
            }

        try:
            # Valider qu'il y a au moins 2 groupes
            if len(source_group_ids) < 2:
                return {
                    "success": False,
                    "message": "Au moins 2 groupes sont requis pour la fusion"
                }

            # Vérifier que tous les groupes existent
            for group_id in source_group_ids:
                if not crud_group.check_group_exists(connection, group_id):
                    return {
                        "success": False,
                        "message": f"Le groupe {group_id} n'existe pas ou est supprimé"
                    }

            # Créer le nouveau groupe
            new_group_data = {
                "name": new_group_name,
                "description": description,
                "created_by": created_by
            }
            new_group_id = crud_group.create(connection, new_group_data)

            if not new_group_id:
                return {
                    "success": False,
                    "message": "Erreur lors de la création du nouveau groupe"
                }

            # Récupérer tous les customers uniques des groupes sources
            unique_customer_ids = crud_group.get_unique_customers_from_groups(
                connection, source_group_ids
            )

            # Ajouter tous les customers au nouveau groupe
            added_count = 0
            for customer_id in unique_customer_ids:
                if crud_group.add_customer_to_group(connection, customer_id, new_group_id, created_by):
                    added_count += 1

            # Récupérer le groupe créé
            new_group = crud_group.get_by_id(connection, new_group_id)

            return {
                "success": True,
                "message": f"Fusion réussie : {added_count} clients ajoutés au nouveau groupe",
                "new_group": new_group,
                "source_group_ids": source_group_ids,
                "total_customers": added_count
            }

        except Exception as e:
            print(f"Erreur lors de la fusion des groupes : {e}")
            return {
                "success": False,
                "message": f"Erreur lors de la fusion : {str(e)}"
            }
        finally:
            connection.close()


group_repository = GroupRepository()
