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

