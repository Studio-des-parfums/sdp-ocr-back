from typing import Optional

from app.database import get_connection
from app.crud import crud_device


def register_device(
    device_id: str,
    device_name: Optional[str] = None,
) -> Optional[dict]:
    conn = get_connection()
    if not conn:
        return None
    try:
        return crud_device.register(conn, device_id, device_name)
    finally:
        conn.close()


def verify_device(device_id: str) -> Optional[dict]:
    conn = get_connection()
    if not conn:
        return None
    try:
        return crud_device.verify(conn, device_id)
    finally:
        conn.close()


def get_all_devices() -> list[dict]:
    conn = get_connection()
    if not conn:
        return []
    try:
        return crud_device.get_all(conn)
    finally:
        conn.close()


def approve_device(device_id: int) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        return crud_device.approve(conn, device_id)
    finally:
        conn.close()


def reject_device(device_id: int) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        return crud_device.reject(conn, device_id)
    finally:
        conn.close()


def rename_device(device_id: int, device_name: str) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        return crud_device.rename(conn, device_id, device_name)
    finally:
        conn.close()
