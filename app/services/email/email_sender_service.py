import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from typing import Optional, List, Dict
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
        is_html: bool = False,
        attachments: List[Dict] = None,
        inline_images: List[Dict] = None
    ) -> MIMEMultipart:
        """
        Creer un message email avec support des pieces jointes et images inline.

        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            body: Corps du message
            is_html: True si le body est en HTML
            attachments: Liste de dict avec 'filename', 'content' (bytes), 'mime_type'
            inline_images: Liste de dict avec 'cid', 'content' (bytes), 'mime_type'
        """
        # Utiliser 'related' pour les images inline, sinon 'mixed' pour les pieces jointes
        if inline_images:
            message = MIMEMultipart("related")
        elif attachments:
            message = MIMEMultipart("mixed")
        else:
            message = MIMEMultipart("alternative")

        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email

        # Ajouter le corps du message
        if inline_images:
            # Pour les images inline, on doit imbriquer le HTML dans une partie alternative
            msg_alternative = MIMEMultipart("alternative")
            content_type = "html" if is_html else "plain"
            msg_alternative.attach(MIMEText(body, content_type, "utf-8"))
            message.attach(msg_alternative)
        else:
            content_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, content_type, "utf-8"))

        # Ajouter les images inline avec Content-ID
        if inline_images:
            for img in inline_images:
                mime_image = MIMEImage(img["content"], _subtype=img.get("subtype", "png"))
                mime_image.add_header("Content-ID", f"<{img['cid']}>")
                mime_image.add_header("Content-Disposition", "inline", filename=img.get("filename", "image.png"))
                message.attach(mime_image)

        # Ajouter les pieces jointes
        if attachments:
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment['filename']}"
                )
                message.attach(part)

        return message

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: List[Dict] = None,
        inline_images: List[Dict] = None
    ) -> dict:
        """
        Envoyer un email avec support des pieces jointes et images inline.

        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            body: Corps du message (texte ou HTML)
            is_html: True si le body est en HTML
            attachments: Liste de pieces jointes [{'filename': 'doc.pdf', 'content': bytes}]
            inline_images: Liste d'images inline [{'cid': 'pyramid', 'content': bytes, 'subtype': 'png'}]

        Returns:
            dict avec success (bool) et message (str)
        """
        try:
            if not self.smtp_user or not self.smtp_password:
                return {
                    "success": False,
                    "message": "Configuration SMTP manquante (SMTP_USER ou SMTP_PASSWORD)"
                }

            message = self._create_message(
                to_email, subject, body, is_html,
                attachments=attachments,
                inline_images=inline_images
            )

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())

            return {
                "success": True,
                "message": f"Email envoye avec succes a {to_email}"
            }

        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": "Erreur d'authentification SMTP. Verifiez les identifiants."
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
            <p>Ceci est un email de test envoye depuis <strong>SDP OCR Backend</strong>.</p>
            <p>Si vous recevez ce message, la configuration email fonctionne correctement.</p>
            <hr style="border: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">
                Ce message a ete envoye automatiquement. Merci de ne pas y repondre.
            </p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, body, is_html=True)


# Instance singleton
email_sender_service = EmailSenderService()
