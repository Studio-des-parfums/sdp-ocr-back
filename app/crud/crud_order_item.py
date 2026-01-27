from typing import Dict, Any, Optional, List
import pymysql


def create(connection: pymysql.connections.Connection,
           item_data: Dict[str, Any]) -> Optional[int]:
    """Créer un nouvel item de commande"""
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO order_items (name, quantity, order_id)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            item_data.get('name'),
            item_data.get('quantity'),
            item_data.get('order_id')
        ))
        connection.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Erreur création item de commande : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def create_many(connection: pymysql.connections.Connection,
                order_id: int,
                items: List[Dict[str, Any]]) -> bool:
    """Créer plusieurs items de commande"""
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO order_items (name, quantity, order_id)
            VALUES (%s, %s, %s)
        """
        for item in items:
            cursor.execute(query, (
                item.get('name'),
                item.get('quantity'),
                order_id
            ))
        connection.commit()
        return True
    except Exception as e:
        print(f"Erreur création items de commande : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def get_by_id(connection: pymysql.connections.Connection,
              item_id: int) -> Optional[Dict]:
    """Récupérer un item de commande par son ID"""
    try:
        cursor = connection.cursor()
        query = "SELECT * FROM order_items WHERE id = %s"
        cursor.execute(query, (item_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Erreur récupération item de commande : {e}")
        return None
    finally:
        cursor.close()


def get_by_order_id(connection: pymysql.connections.Connection,
                    order_id: int) -> List[Dict]:
    """Récupérer tous les items d'une commande"""
    try:
        cursor = connection.cursor()
        query = "SELECT * FROM order_items WHERE order_id = %s ORDER BY id ASC"
        cursor.execute(query, (order_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Erreur récupération items de commande : {e}")
        return []
    finally:
        cursor.close()


def update(connection: pymysql.connections.Connection,
           item_id: int, item_data: Dict[str, Any]) -> bool:
    """Mettre à jour un item de commande"""
    try:
        cursor = connection.cursor()
        clean_data = {k: v for k, v in item_data.items()
                      if v is not None and k != 'order_id'}
        if not clean_data:
            return False

        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        values = list(clean_data.values()) + [item_id]

        query = f"""
            UPDATE order_items
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        cursor.execute(query, values)
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur mise à jour item de commande : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: pymysql.connections.Connection,
           item_id: int) -> bool:
    """Supprimer un item de commande"""
    try:
        cursor = connection.cursor()
        query = "DELETE FROM order_items WHERE id = %s"
        cursor.execute(query, (item_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur suppression item de commande : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete_by_order_id(connection: pymysql.connections.Connection,
                       order_id: int) -> bool:
    """Supprimer tous les items d'une commande"""
    try:
        cursor = connection.cursor()
        query = "DELETE FROM order_items WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        connection.commit()
        return True
    except Exception as e:
        print(f"Erreur suppression items de commande : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
