from typing import Dict, Any, Optional, List, Tuple
import pymysql


def create(connection: pymysql.connections.Connection,
           role_data: Dict[str, Any]) -> Optional[int]:
    """Créer un nouveau rôle"""
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO roles (name, csv, pdf, email_sending, customer_validation)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            role_data.get('name'),
            role_data.get('csv', 0),
            role_data.get('pdf', 0),
            role_data.get('email_sending', False),
            role_data.get('customer_validation', False)
        ))
        connection.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Erreur création rôle : {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()


def get_by_id(connection: pymysql.connections.Connection,
              role_id: int) -> Optional[Dict]:
    """Récupérer un rôle par son ID"""
    try:
        cursor = connection.cursor()
        query = "SELECT * FROM roles WHERE id = %s"
        cursor.execute(query, (role_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Erreur récupération rôle : {e}")
        return None
    finally:
        cursor.close()


def get_all(connection: pymysql.connections.Connection,
            page: int = 1, size: int = 10,
            search: Optional[str] = None) -> Tuple[List[Dict], int]:
    """Récupérer tous les rôles avec pagination"""
    try:
        cursor = connection.cursor()

        where_conditions = []
        params = []
        if search:
            where_conditions.append("name LIKE %s")
            search_param = f"%{search}%"
            params.append(search_param)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM roles {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Récupérer les résultats paginés
        offset = (page - 1) * size
        query = f"""
            SELECT * FROM roles {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([size, offset])
        cursor.execute(query, params)
        return cursor.fetchall(), total
    except Exception as e:
        print(f"Erreur récupération rôles : {e}")
        return [], 0
    finally:
        cursor.close()


def update(connection: pymysql.connections.Connection,
           role_id: int, role_data: Dict[str, Any]) -> bool:
    """Mettre à jour un rôle"""
    try:
        cursor = connection.cursor()
        clean_data = {k: v for k, v in role_data.items()
                      if v is not None}
        if not clean_data:
            return False

        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        values = list(clean_data.values()) + [role_id]

        query = f"""
            UPDATE roles
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        cursor.execute(query, values)
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur mise à jour rôle : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete(connection: pymysql.connections.Connection,
           role_id: int) -> bool:
    """Supprimer un rôle définitivement"""
    try:
        cursor = connection.cursor()
        query = "DELETE FROM roles WHERE id = %s"
        cursor.execute(query, (role_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur suppression rôle : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
