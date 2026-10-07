"""
Job périodique : annule les sessions tablette 'active' restées inactives trop
longtemps (client parti sans terminer ni annuler explicitement — sinon elles
s'accumulent indéfiniment et polluent la liste des sessions actives côté
superviseur).

Tourne dans le process web via APScheduler (pas de worker/cron séparé déployé).
"""
from apscheduler.schedulers.background import BackgroundScheduler

from app.database.connection import get_connection
from app.crud import crud_session

INACTIVE_HOURS = 2
CHECK_INTERVAL_MINUTES = 30

_scheduler = None


def expire_stale_sessions():
    """Annule les sessions actives sans activité depuis INACTIVE_HOURS."""
    connection = None
    try:
        connection = get_connection()
        if not connection:
            print("session_scheduler: pas de connexion BDD, job ignoré")
            return

        count = crud_session.expire_stale_sessions(connection, inactive_hours=INACTIVE_HOURS)
        if count:
            print(f"session_scheduler: {count} session(s) inactive(s) annulée(s)")

    except Exception as e:
        print(f"session_scheduler: erreur job : {e}")
    finally:
        if connection:
            connection.close()


def start_session_scheduler():
    """Démarre le scheduler en arrière-plan (appelé une fois au démarrage de l'app)."""
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        expire_stale_sessions,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="expire_stale_sessions",
    )
    _scheduler.start()
