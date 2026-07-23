from typing import Optional
import pymysql


def register(
    connection: pymysql.connections.Connection,
    device_id: str,
    device_name: Optional[str] = None,
) -> Optional[dict]:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO devices (device_id, device_name, status)
            VALUES (%s, %s, 'pending')
            ON DUPLICATE KEY UPDATE device_name = COALESCE(%s, device_name), last_seen_at = NOW()
        """
        cursor.execute(query, (device_id, device_name, device_name))
        connection.commit()

        cursor.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Erreur enregistrement appareil : {e}")
        connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()


def verify(connection: pymysql.connections.Connection, device_id: str) -> Optional[dict]:
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
        device = cursor.fetchone()
        if device:
            cursor.execute(
                "UPDATE devices SET last_seen_at = NOW() WHERE device_id = %s",
                (device_id,),
            )
            connection.commit()
        return device
    except Exception as e:
        print(f"Erreur verification appareil : {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def get_all(connection: pymysql.connections.Connection) -> list[dict]:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            SELECT id, device_id, device_name, registered_at, last_seen_at, status, decided_at
            FROM devices
            ORDER BY FIELD(status, 'pending', 'approved', 'rejected'), registered_at DESC
        """
        cursor.execute(query)
        return cursor.fetchall() or []
    except Exception as e:
        print(f"Erreur recuperation appareils : {e}")
        return []
    finally:
        if cursor:
            cursor.close()


def approve(connection: pymysql.connections.Connection, device_id: int) -> bool:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            UPDATE devices
            SET status = 'approved', decided_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, (device_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur approbation appareil {device_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()


def rename(connection: pymysql.connections.Connection, device_id: int, device_name: str) -> bool:
    cursor = None
    try:
        cursor = connection.cursor()
        query = "UPDATE devices SET device_name = %s WHERE id = %s"
        cursor.execute(query, (device_name, device_id))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur renommage appareil {device_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()


def reject(connection: pymysql.connections.Connection, device_id: int) -> bool:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            UPDATE devices
            SET status = 'rejected', decided_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, (device_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur rejet appareil {device_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
