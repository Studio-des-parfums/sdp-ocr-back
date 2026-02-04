from typing import Dict, Any, Optional, List, Tuple
import pymysql


def create(connection: pymysql.connections.Connection, group_data: Dict[str, Any]) -> Optional[int]:
    """
    Crée un nouveau groupe dans la base de données

    Args:
        connection: Connexion MySQL
        group_data: Données du groupe (name, description, created_by)

    Returns:
        ID du groupe créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO `groups` (name, description, created_by)
            VALUES (%s, %s, %s)
        """

        cursor.execute(query, (
            group_data.get('name'),
            group_data.get('description'),
            group_data.get('created_by')
        ))

        connection.commit()
        group_id = cursor.lastrowid

        return group_id

    except Exception as e:
        print(f"Erreur création groupe : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_name(connection: pymysql.connections.Connection, name: str) -> Optional[Dict[str, Any]]:
    """
    Recherche un groupe par son nom (case-insensitive, non supprimé)

    Args:
        connection: Connexion MySQL
        name: Nom du groupe à chercher

    Returns:
        Dictionnaire avec les données du groupe ou None
    """
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM `groups` WHERE LOWER(name) = LOWER(%s) AND is_deleted = FALSE LIMIT 1"
        cursor.execute(query, (name,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur recherche groupe par nom : {e}")
        return None
    finally:
        cursor.close()


def get_by_id(connection: pymysql.connections.Connection, group_id: int,
              include_deleted: bool = False) -> Optional[Dict[str, Any]]:
    """
    Récupère un groupe par son ID

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe
        include_deleted: Inclure les groupes supprimés

    Returns:
        Dictionnaire avec les données du groupe ou None
    """
    try:
        cursor = connection.cursor()

        where_clause = "WHERE id = %s"
        if not include_deleted:
            where_clause += " AND is_deleted = FALSE"

        query = f"SELECT * FROM `groups` {where_clause}"
        cursor.execute(query, (group_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération groupe : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: pymysql.connections.Connection, page: int = 1, size: int = 10,
            search: Optional[str] = None, include_deleted: bool = False) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les groupes avec pagination et recherche

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page
        search: Terme de recherche
        include_deleted: Inclure les groupes supprimés

    Returns:
        Tuple (liste des groupes, total)
    """
    try:
        cursor = connection.cursor()

        # Construire la clause WHERE
        where_conditions = []
        params = []

        # Filtrer les supprimés sauf si demandé
        if not include_deleted:
            where_conditions.append("is_deleted = FALSE")

        # Recherche
        if search:
            where_conditions.append("(name LIKE %s OR description LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM `groups` {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT * FROM `groups` {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])

        cursor.execute(query, params)
        groups = cursor.fetchall()

        return groups, total

    except Exception as e:
        print(f"Erreur récupération groupes : {e}")
        return [], 0
    finally:
        cursor.close()


def update(connection: pymysql.connections.Connection, group_id: int,
           group_data: Dict[str, Any]) -> bool:
    """
    Met à jour un groupe

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe
        group_data: Nouvelles données (name, description)

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in group_data.items() if v is not None and v != ""}

        if not clean_data:
            return False

        # Construire la requête UPDATE avec updated_at automatique
        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")

        values = list(clean_data.values())
        values.append(group_id)

        query = f"""
            UPDATE `groups`
            SET {', '.join(set_clauses)}
            WHERE id = %s AND is_deleted = FALSE
        """

        cursor.execute(query, values)
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur mise à jour groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def soft_delete(connection: pymysql.connections.Connection, group_id: int) -> bool:
    """
    Suppression logique d'un groupe (is_deleted = TRUE)

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = """
            UPDATE `groups`
            SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND is_deleted = FALSE
        """

        cursor.execute(query, (group_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur suppression groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def restore(connection: pymysql.connections.Connection, group_id: int) -> bool:
    """
    Restaure un groupe supprimé (is_deleted = FALSE)

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = """
            UPDATE `groups`
            SET is_deleted = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND is_deleted = TRUE
        """

        cursor.execute(query, (group_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur restauration groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


# ======================================================================
# CUSTOMER-GROUP RELATIONS
# ======================================================================

def add_customer_to_group(connection: pymysql.connections.Connection, customer_id: int,
                         group_id: int, added_by: int) -> bool:
    """
    Ajoute un customer à un groupe

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer
        group_id: ID du groupe
        added_by: ID de l'utilisateur qui ajoute

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Vérifier si la relation existe déjà
        cursor.execute(
            "SELECT id FROM customer_groups WHERE customer_id = %s AND group_id = %s",
            (customer_id, group_id)
        )
        if cursor.fetchone():
            return False  # Relation existe déjà

        # Insérer la relation
        cursor.execute("""
            INSERT INTO customer_groups (customer_id, group_id, added_by)
            VALUES (%s, %s, %s)
        """, (customer_id, group_id, added_by))

        connection.commit()
        return True

    except Exception as e:
        print(f"Erreur ajout customer au groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def remove_customer_from_group(connection: pymysql.connections.Connection, customer_id: int,
                               group_id: int) -> bool:
    """
    Retire un customer d'un groupe

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer
        group_id: ID du groupe

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM customer_groups
            WHERE customer_id = %s AND group_id = %s
        """, (customer_id, group_id))

        connection.commit()
        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur retrait customer du groupe : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def get_group_customers(connection: pymysql.connections.Connection, group_ids: List[int],
                       page: int = 1, size: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les customers d'un ou plusieurs groupes avec pagination

    Args:
        connection: Connexion MySQL
        group_ids: Liste des IDs des groupes
        page: Numéro de page
        size: Taille de page

    Returns:
        Tuple (liste des customers, total)
    """
    try:
        cursor = connection.cursor()

        if not group_ids:
            return [], 0

        # Créer la clause IN pour les group_ids
        placeholders = ', '.join(['%s'] * len(group_ids))

        # Compter le total (DISTINCT pour éviter les doublons si un client est dans plusieurs groupes)
        count_query = f"""
            SELECT COUNT(DISTINCT c.id) as total
            FROM customer_groups cg
            JOIN customers c ON cg.customer_id = c.id
            WHERE cg.group_id IN ({placeholders})
        """
        cursor.execute(count_query, group_ids)
        total = cursor.fetchone()['total']

        # Récupérer les données avec pagination (DISTINCT pour éviter les doublons)
        offset = (page - 1) * size
        query = f"""
            SELECT DISTINCT c.*,
                   MIN(cg.added_at) as added_at,
                   MIN(cg.added_by) as added_by
            FROM customer_groups cg
            JOIN customers c ON cg.customer_id = c.id
            WHERE cg.group_id IN ({placeholders})
            GROUP BY c.id
            ORDER BY added_at DESC
            LIMIT %s OFFSET %s
        """

        params = list(group_ids) + [size, offset]
        cursor.execute(query, params)
        customers = cursor.fetchall()

        return customers, total

    except Exception as e:
        print(f"Erreur récupération customers des groupes : {e}")
        return [], 0
    finally:
        cursor.close()


def get_customer_groups(connection: pymysql.connections.Connection, customer_id: int) -> List[Dict[str, Any]]:
    """
    Récupère tous les groupes d'un customer

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        Liste des groupes
    """
    try:
        cursor = connection.cursor()

        query = """
            SELECT g.*, cg.added_at, cg.added_by
            FROM customer_groups cg
            JOIN `groups` g ON cg.group_id = g.id
            WHERE cg.customer_id = %s AND g.is_deleted = FALSE
            ORDER BY cg.added_at DESC
        """

        cursor.execute(query, (customer_id,))
        groups = cursor.fetchall()

        return groups

    except Exception as e:
        print(f"Erreur récupération groupes du customer : {e}")
        return []
    finally:
        cursor.close()


def check_group_exists(connection: pymysql.connections.Connection, group_id: int) -> bool:
    """
    Vérifie si un groupe existe et n'est pas supprimé

    Args:
        connection: Connexion MySQL
        group_id: ID du groupe

    Returns:
        True si le groupe existe, False sinon
    """
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM `groups` WHERE id = %s AND is_deleted = FALSE", (group_id,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification groupe : {e}")
        return False
    finally:
        cursor.close()


def check_customer_exists(connection: pymysql.connections.Connection, customer_id: int) -> bool:
    """
    Vérifie si un customer existe

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        True si le customer existe, False sinon
    """
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM customers WHERE id = %s", (customer_id,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification customer : {e}")
        return False
    finally:
        cursor.close()


def get_unique_customers_from_groups(connection: pymysql.connections.Connection, 
                                     group_ids: List[int]) -> List[int]:
    """
    Récupère tous les IDs de customers uniques présents dans plusieurs groupes

    Args:
        connection: Connexion MySQL
        group_ids: Liste des IDs des groupes

    Returns:
        Liste des IDs de customers uniques
    """
    try:
        cursor = connection.cursor()

        if not group_ids:
            return []

        # Créer la clause IN pour les group_ids
        placeholders = ', '.join(['%s'] * len(group_ids))

        query = f"""
            SELECT DISTINCT customer_id
            FROM customer_groups
            WHERE group_id IN ({placeholders})
        """

        cursor.execute(query, group_ids)
        results = cursor.fetchall()

        # Extraire les IDs de la liste de dictionnaires
        customer_ids = [row['customer_id'] for row in results]

        return customer_ids

    except Exception as e:
        print(f"Erreur récupération customers uniques : {e}")
        return []
    finally:
        cursor.close()
