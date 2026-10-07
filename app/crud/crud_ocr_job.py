from typing import Dict, Any, Optional
import json
import pymysql


def create(
    connection: pymysql.connections.Connection,
    job_id: str,
    filename: str
) -> bool:
    """
    Crée un nouveau job OCR en base, statut initial 'pending'

    Args:
        connection: Connexion MySQL
        job_id: UUID du job
        filename: Nom du fichier PDF traité

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO ocr_jobs (id, status, progress, total_pages, filename)
            VALUES (%s, 'pending', 0, 0, %s)
        """
        cursor.execute(query, (job_id, filename))
        connection.commit()

        return True

    except Exception as e:
        print(f"Erreur création ocr_job : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def get_by_id(
    connection: pymysql.connections.Connection,
    job_id: str
) -> Optional[Dict[str, Any]]:
    """
    Récupère un job OCR par son ID

    Args:
        connection: Connexion MySQL
        job_id: UUID du job

    Returns:
        Dictionnaire avec les données du job (result/error désérialisés) ou None
    """
    try:
        cursor = connection.cursor()

        query = """
            SELECT id, status, progress, total_pages, filename, result, error, created_at
            FROM ocr_jobs
            WHERE id = %s
        """
        cursor.execute(query, (job_id,))
        row = cursor.fetchone()

        if not row:
            return None

        if row.get('result'):
            row['result'] = json.loads(row['result'])

        return row

    except Exception as e:
        print(f"Erreur récupération ocr_job : {e}")
        return None
    finally:
        cursor.close()


def update(
    connection: pymysql.connections.Connection,
    job_id: str,
    job_data: Dict[str, Any]
) -> bool:
    """
    Met à jour un job OCR (statut, progression, résultat, erreur...)

    Args:
        connection: Connexion MySQL
        job_id: UUID du job
        job_data: Champs à mettre à jour (result est sérialisé en JSON automatiquement)

    Returns:
        True si succès, False sinon
    """
    try:
        cursor = connection.cursor()

        clean_data = dict(job_data)
        if 'result' in clean_data and clean_data['result'] is not None:
            clean_data['result'] = json.dumps(clean_data['result'], ensure_ascii=False)

        if not clean_data:
            return False

        set_clauses = [f"{col} = %s" for col in clean_data.keys()]
        values = list(clean_data.values())
        values.append(job_id)

        query = f"""
            UPDATE ocr_jobs
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        cursor.execute(query, values)
        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Erreur mise à jour ocr_job : {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def delete_older_than(
    connection: pymysql.connections.Connection,
    days: int
) -> int:
    """
    Supprime les jobs OCR plus vieux que N jours (nettoyage périodique)

    Args:
        connection: Connexion MySQL
        days: Âge en jours au-delà duquel un job est supprimé

    Returns:
        Nombre de jobs supprimés
    """
    try:
        cursor = connection.cursor()

        query = "DELETE FROM ocr_jobs WHERE created_at < NOW() - INTERVAL %s DAY"
        cursor.execute(query, (days,))
        connection.commit()

        return cursor.rowcount

    except Exception as e:
        print(f"Erreur nettoyage ocr_jobs : {e}")
        connection.rollback()
        return 0
    finally:
        cursor.close()
