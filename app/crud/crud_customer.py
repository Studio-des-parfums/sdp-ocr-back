from typing import Dict, Any, Optional, List, Tuple
import pymysql


def create(connection: pymysql.connections.Connection, customer_data: Dict[str, Any]) -> Optional[int]:
    """
    Crée un nouveau customer dans la base de données

    Args:
        connection: Connexion MySQL
        customer_data: Données du customer

    Returns:
        ID du customer créé ou None si erreur
    """
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {k: v for k, v in customer_data.items() if v is not None and v != ""}

        if clean_data:
            columns = list(clean_data.keys())
            placeholders = ["%s"] * len(columns)
            values = list(clean_data.values())

            query = f"""
                INSERT INTO customers ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            cursor.execute(query, values)
        else:
            # Insertion ligne vide
            query = "INSERT INTO customers () VALUES ()"
            cursor.execute(query)

        connection.commit()
        customer_id = cursor.lastrowid

        return customer_id

    except Exception as e:
        print(f"Erreur création customer : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(connection: pymysql.connections.Connection, customer_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son ID

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM customers WHERE id = %s"
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer : {e}")
        return None
    finally:
        cursor.close()


def get_by_email(connection: pymysql.connections.Connection, email: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son email

    Args:
        connection: Connexion MySQL
        email: Email du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM customers WHERE email = %s LIMIT 1"
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par email : {e}")
        return None
    finally:
        cursor.close()


def get_by_phone(connection: pymysql.connections.Connection, phone: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par son téléphone

    Args:
        connection: Connexion MySQL
        phone: Téléphone du customer

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    try:
        cursor = connection.cursor()

        query = "SELECT * FROM customers WHERE phone = %s LIMIT 1"
        cursor.execute(query, (phone,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par téléphone : {e}")
        return None
    finally:
        cursor.close()


def get_by_phone_normalized(connection: pymysql.connections.Connection, phone: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un customer par téléphone en ignorant tout caractère non numérique
    (espaces, tirets, points) des deux côtés de la comparaison.

    Utile car les numéros sont stockés formatés (ex: "06 66 69 48 31") mais
    peuvent être saisis sans formatage (ex: "0666694831").

    Args:
        connection: Connexion MySQL
        phone: Téléphone du customer, formaté ou non

    Returns:
        Dictionnaire avec les données du customer ou None
    """
    import re
    digits_only = re.sub(r"\D", "", phone or "")
    if not digits_only:
        return None

    try:
        cursor = connection.cursor()

        query = """
            SELECT * FROM customers
            WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                phone, ' ', ''), '-', ''), '.', ''), '(', ''), ')', ''
            ) = %s
            LIMIT 1
        """
        cursor.execute(query, (digits_only,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération customer par téléphone normalisé : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: pymysql.connections.Connection, page: int = 1, size: int = 10,
            search: Optional[str] = None, v2: bool = False) -> Tuple[List[Dict[str, Any]], int]:
    """
    Récupère tous les customers avec pagination et recherche

    Args:
        connection: Connexion MySQL
        page: Numéro de page
        size: Taille de page
        search: Terme de recherche (nom, email, téléphone, ville, référence de formule)
        v2: Filtre par version du formulaire

    Returns:
        Tuple (liste des customers, total)
    """
    try:
        cursor = connection.cursor()

        conditions = ["customers.v2 = %s"]
        params = [v2]

        if search:
            search_param = f"%{search}%"
            conditions.append("""
                (customers.first_name LIKE %s OR customers.last_name LIKE %s
                OR customers.email LIKE %s OR customers.phone LIKE %s OR customers.city LIKE %s
                OR customers.id IN (
                    SELECT formula.customer_id FROM formula WHERE formula.reference LIKE %s
                ))
            """)
            params.extend([search_param] * 6)

        where_clause = "WHERE " + " AND ".join(conditions)

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM customers {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT * FROM customers {where_clause}
            ORDER BY customers.id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])

        cursor.execute(query, params)
        customers = cursor.fetchall()

        return customers, total

    except Exception as e:
        print(f"Erreur récupération customers : {e}")
        return [], 0
    finally:
        cursor.close()


def update(connection: pymysql.connections.Connection, customer_id: int,
           customer_data: Dict[str, Any]) -> bool:
    """
    Met à jour un customer

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer
        customer_data: Nouvelles données

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        # Vérifier d'abord que le customer existe
        check_query = "SELECT id FROM customers WHERE id = %s"
        cursor.execute(check_query, (customer_id,))
        if not cursor.fetchone():
            return False

        # Filtrer les valeurs None/vides MAIS garder les valeurs explicitement None pour les nettoyer
        clean_data = {}
        for k, v in customer_data.items():
            # Garder toutes les valeurs sauf les chaînes vides
            if v != "":
                clean_data[k] = v

        if not clean_data:
            # Pas de données à mettre à jour, mais le customer existe
            return True

        # Construire la requête UPDATE
        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        values = list(clean_data.values())
        values.append(customer_id)  # Pour le WHERE

        query = f"""
            UPDATE customers
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """

        cursor.execute(query, values)
        connection.commit()

        # Si rowcount == 0, ça peut être parce que les valeurs étaient déjà identiques
        # Mais on a vérifié l'existence au début, donc on retourne True
        return True

    except Exception as e:
        print(f"Erreur mise à jour customer : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: pymysql.connections.Connection, customer_id: int) -> bool:
    """
    Supprime un customer

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "DELETE FROM customers WHERE id = %s"
        cursor.execute(query, (customer_id,))
        connection.commit()

        success = cursor.rowcount > 0
        return success

    except Exception as e:
        print(f"Erreur suppression customer : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def check_duplicate_email(connection: pymysql.connections.Connection, email: str) -> bool:
    """
    Vérifie si un email existe déjà

    Args:
        connection: Connexion MySQL
        email: Email à vérifier

    Returns:
        True si l'email existe, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "SELECT id FROM customers WHERE email = %s LIMIT 1"
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification email : {e}")
        return False
    finally:
        cursor.close()


def check_duplicate_phone(connection: pymysql.connections.Connection, phone: str) -> bool:
    """
    Vérifie si un téléphone existe déjà

    Args:
        connection: Connexion MySQL
        phone: Téléphone à vérifier

    Returns:
        True si le téléphone existe, False sinon
    """
    try:
        cursor = connection.cursor()

        query = "SELECT id FROM customers WHERE phone = %s LIMIT 1"
        cursor.execute(query, (phone,))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print(f"Erreur vérification téléphone : {e}")
        return False
    finally:
        cursor.close()
