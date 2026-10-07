from typing import Dict, Any, Optional
from app.database import get_connection
from app.crud import crud_ocr_job


class OcrJobRepository:
    """
    Repository pour gérer l'accès aux données ocr_jobs (Data Access Layer).

    Remplace l'ancien store en mémoire (_jobs dict) : persiste l'état du job
    en base pour qu'il survive aux redémarrages/redéploiements du process et
    reste accessible quel que soit le réplica qui reçoit la requête de polling.
    """

    def create_job(self, job_id: str, filename: str) -> bool:
        connection = get_connection()
        if not connection:
            return False

        try:
            return crud_ocr_job.create(connection, job_id, filename)
        finally:
            connection.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        connection = get_connection()
        if not connection:
            return None

        try:
            return crud_ocr_job.get_by_id(connection, job_id)
        finally:
            connection.close()

    def update_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        connection = get_connection()
        if not connection:
            return False

        try:
            return crud_ocr_job.update(connection, job_id, job_data)
        finally:
            connection.close()

    def cleanup_old_jobs(self, days: int = 7) -> int:
        connection = get_connection()
        if not connection:
            return 0

        try:
            return crud_ocr_job.delete_older_than(connection, days)
        finally:
            connection.close()


ocr_job_repository = OcrJobRepository()
