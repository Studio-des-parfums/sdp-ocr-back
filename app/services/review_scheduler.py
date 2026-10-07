"""
Job périodique : envoie une demande d'avis Google aux clients dont la formule
(parcours tablette) a été créée il y a plus de 24h, une seule fois par formule.

Tourne dans le process web via APScheduler (pas de worker/cron séparé déployé).
Idempotent : chaque formule traitée est marquée `review_email_sent_at` avant de
passer à la suivante, pour ne jamais redemander un avis deux fois.
"""
from apscheduler.schedulers.background import BackgroundScheduler

from app.database.connection import get_connection
from app.crud import crud_formula
from app.services.email.review_request_service import send_review_request_email

REVIEW_DELAY_HOURS = 24
CHECK_INTERVAL_MINUTES = 15

_scheduler = None


def send_pending_review_emails():
    """Parcourt les formules éligibles et envoie l'email d'avis pour chacune."""
    connection = None
    try:
        connection = get_connection()
        if not connection:
            print("review_scheduler: pas de connexion BDD, job ignoré")
            return

        pending = crud_formula.get_pending_review_emails(connection, delay_hours=REVIEW_DELAY_HOURS)
        for item in pending:
            # Marqué avant l'envoi : en cas de crash/retry on ne spamme jamais deux fois,
            # au prix (acceptable) de manquer un envoi en cas d'échec Resend ponctuel.
            crud_formula.mark_review_email_sent(connection, item["formula_id"])
            result = send_review_request_email(
                to_email=item["email"],
                first_name=item.get("first_name") or "",
                perfume_name=item.get("perfume_name"),
            )
            if not result.get("success"):
                print(f"review_scheduler: échec envoi formule {item['formula_id']} : {result.get('message')}")

    except Exception as e:
        print(f"review_scheduler: erreur job : {e}")
    finally:
        if connection:
            connection.close()


def start_review_scheduler():
    """Démarre le scheduler en arrière-plan (appelé une fois au démarrage de l'app)."""
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        send_pending_review_emails,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="send_pending_review_emails",
    )
    _scheduler.start()
