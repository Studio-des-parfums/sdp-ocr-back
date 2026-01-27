from typing import Dict, Any, Optional, List, Tuple
import pymysql


def create(connection: pymysql.connections.Connection,
           order_data: Dict[str, Any]) -> Optional[int]:
    """Créer une nouvelle commande"""
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO orders (customer_id, formula_id, comment, allergy, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            order_data.get('customer_id'),
            order_data.get('formula_id'),
            order_data.get('comment'),
            order_data.get('allergy'),
            order_data.get('status', 'PENDING')
        ))
        connection.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Erreur création commande : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(connection: pymysql.connections.Connection,
              order_id: int) -> Optional[Dict]:
    """Récupérer une commande par son ID"""
    try:
        cursor = connection.cursor()
        query = "SELECT * FROM orders WHERE id = %s"
        cursor.execute(query, (order_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Erreur récupération commande : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: pymysql.connections.Connection,
            page: int = 1, size: int = 10,
            search: Optional[str] = None,
            customer_id: Optional[int] = None,
            status: Optional[str] = None) -> Tuple[List[Dict], int]:
    """Récupérer toutes les commandes avec pagination"""
    try:
        cursor = connection.cursor()

        where_conditions = []
        params = []

        if search:
            where_conditions.append("comment LIKE %s")
            params.append(f"%{search}%")

        if customer_id:
            where_conditions.append("customer_id = %s")
            params.append(customer_id)

        if status:
            where_conditions.append("status = %s")
            params.append(status)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM orders {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT * FROM orders {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])
        cursor.execute(query, params)
        return cursor.fetchall(), total
    except Exception as e:
        print(f"Erreur récupération commandes : {e}")
        return [], 0
    finally:
        cursor.close()


def update(connection: pymysql.connections.Connection,
           order_id: int, order_data: Dict[str, Any]) -> bool:
    """Mettre à jour une commande"""
    try:
        cursor = connection.cursor()
        clean_data = {k: v for k, v in order_data.items()
                      if v is not None}
        if not clean_data:
            return False

        set_clauses = [f"`{col}` = %s" for col in clean_data.keys()]
        values = list(clean_data.values()) + [order_id]

        query = f"""
            UPDATE orders
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        cursor.execute(query, values)
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur mise à jour commande : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: pymysql.connections.Connection,
           order_id: int) -> bool:
    """Supprimer une commande définitivement"""
    try:
        cursor = connection.cursor()
        query = "DELETE FROM orders WHERE id = %s"
        cursor.execute(query, (order_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur suppression commande : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
