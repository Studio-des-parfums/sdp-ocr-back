from typing import Optional
import pymysql


def _insert_note(
    connection: pymysql.connections.Connection,
    table_name: str,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    """
    Helper générique pour insérer une note dans une table donnée.
    """
    cursor = None
    try:
        cursor = connection.cursor()

        # Filtrer les valeurs None/vides
        clean_data = {
            "name": name,
            "quantity": quantity,
            "formula_id": formula_id,
        }
        clean_data = {k: v for k, v in clean_data.items() if v is not None and v != ""}

        columns = list(clean_data.keys())
        placeholders = ["%s"] * len(columns)
        values = list(clean_data.values())

        if not columns:
            return None

        query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        cursor.execute(query, values)

        connection.commit()
        note_id = cursor.lastrowid

        return note_id

    except Exception as e:
        print(f"Erreur création note dans {table_name} : {e}")
        if connection.open:
            connection.rollback()
        return None
    finally:
        if cursor is not None:
            cursor.close()


def create_top_note(
    connection: pymysql.connections.Connection,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    return _insert_note(connection, "top_note", formula_id, name, quantity)


def create_heart_note(
    connection: pymysql.connections.Connection,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    return _insert_note(connection, "heart_note", formula_id, name, quantity)


def create_base_note(
    connection: pymysql.connections.Connection,
    formula_id: int,
    name: str,
    quantity: Optional[str],
) -> Optional[int]:
    return _insert_note(connection, "base_note", formula_id, name, quantity)

