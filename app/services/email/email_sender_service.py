import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings


class EmailSenderService:
    """Service pour l'envoi d'emails via SMTP Gmail"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    def _create_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> MIMEMultipart:
        """Creer un message email"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email

        content_type = "html" if is_html else "plain"
        message.attach(MIMEText(body, content_type, "utf-8"))

        return message

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> dict:
        """
        Envoyer un email

        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            body: Corps du message (texte ou HTML)
            is_html: True si le body est en HTML

        Returns:
            dict avec success (bool) et message (str)
        """
        try:
            if not self.smtp_user or not self.smtp_password:
                return {
                    "success": False,
                    "message": "Configuration SMTP manquante (SMTP_USER ou SMTP_PASSWORD)"
                }

            message = self._create_message(to_email, subject, body, is_html)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())

            return {
                "success": True,
                "message": f"Email envoyé avec succès à {to_email}"
            }

        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": "Erreur d'authentification SMTP. Vérifiez les identifiants."
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "message": f"Erreur SMTP: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur inattendue: {str(e)}"
            }

    def send_test_email(self, to_email: str) -> dict:
        """
        Envoyer un email de test

        Args:
            to_email: Adresse email du destinataire

        Returns:
            dict avec success (bool) et message (str)
        """
        subject = "Test - SDP OCR Backend"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #333;">Email de test</h2>
            <p>Ceci est un email de test envoyé depuis <strong>SDP OCR Backend</strong>.</p>
            <p>Si vous recevez ce message, la configuration email fonctionne correctement.</p>
            <hr style="border: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">
                Ce message a été envoyé automatiquement. Merci de ne pas y répondre.
            </p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, body, is_html=True)


# Instance singleton
email_sender_service = EmailSenderService()
