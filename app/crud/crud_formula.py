from typing import Optional
import pymysql


def create(
    connection: pymysql.connections.Connection,
    customer_id: Optional[int],
    file_id: int,
    customer_review_id: Optional[int] = None,
) -> Optional[int]:
    """
    Crée une nouvelle formule liée à un customer (ou customer_review) et à un fichier.

    Args:
        connection: Connexion MySQL
        customer_id: ID du customer (peut être None si review)
        file_id: ID du fichier source (customer_files.id)
        customer_review_id: ID du customer_review (peut être None si customer)

    Returns:
        ID de la formule créée ou None si erreur
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO formula (customer_id, file_id, customer_review_id)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (customer_id, file_id, customer_review_id))

        connection.commit()
        formula_id = cursor.lastrowid

        return formula_id

    except Exception as e:
        print(f"Erreur création formula : {e}")
        if connection.open:
            connection.rollback()
        return None
    finally:
        if cursor is not None:
            cursor.close()


def get_by_id(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> Optional[dict]:
    """
    Récupère une formule par son ID.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule

    Returns:
        Dictionnaire avec les données de la formule ou None si non trouvée
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, customer_id, file_id, customer_review_id
            FROM formula
            WHERE id = %s
        """
        cursor.execute(query, (formula_id,))
        result = cursor.fetchone()

        return result

    except Exception as e:
        print(f"Erreur récupération formula {formula_id} : {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()


def delete(
    connection: pymysql.connections.Connection,
    formula_id: int,
) -> bool:
    """
    Supprime une formule par son ID.
    Les notes associées sont supprimées automatiquement via CASCADE.

    Args:
        connection: Connexion MySQL
        formula_id: ID de la formule à supprimer

    Returns:
        True si succès, False sinon
    """
    cursor = None
    try:
        cursor = connection.cursor()

        query = """
            DELETE FROM formula
            WHERE id = %s
        """
        cursor.execute(query, (formula_id,))

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur suppression formula {formula_id} : {e}")
        if connection.open:
            connection.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()

