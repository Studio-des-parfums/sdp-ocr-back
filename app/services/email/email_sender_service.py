import base64
import requests
from typing import Optional, List, Dict
from app.core.config import settings

RESEND_API_URL = "https://api.resend.com/emails"


class EmailSenderService:
    """Service pour l'envoi d'emails via l'API Resend"""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.RESEND_FROM_EMAIL
        self.from_name = settings.RESEND_FROM_NAME

    def _build_attachments(
        self,
        attachments: List[Dict] = None,
        inline_images: List[Dict] = None
    ) -> List[Dict]:
        """
        Convertit pièces jointes et images inline au format attendu par Resend
        (content en base64, image inline via content_id référencé par cid: dans le HTML).
        """
        result = []
        for attachment in attachments or []:
            result.append({
                "filename": attachment["filename"],
                "content": base64.b64encode(attachment["content"]).decode("utf-8"),
            })
        for img in inline_images or []:
            result.append({
                "filename": img.get("filename", "image.png"),
                "content": base64.b64encode(img["content"]).decode("utf-8"),
                "content_id": img["cid"],
            })
        return result

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: List[Dict] = None,
        inline_images: List[Dict] = None,
        cc: Optional[str] = None
    ) -> dict:
        """
        Envoyer un email avec support des pieces jointes et images inline.

        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            body: Corps du message (texte ou HTML)
            is_html: True si le body est en HTML
            attachments: Liste de pieces jointes [{'filename': 'doc.pdf', 'content': bytes}]
            inline_images: Liste d'images inline [{'cid': 'pyramid', 'content': bytes, 'filename': '...'}]
            cc: Adresse en copie

        Returns:
            dict avec success (bool) et message (str)
        """
        try:
            if not self.api_key or not self.from_email:
                return {
                    "success": False,
                    "message": "Configuration Resend manquante (RESEND_API_KEY ou RESEND_FROM_EMAIL)"
                }

            payload = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
            }
            payload["html" if is_html else "text"] = body

            if cc:
                payload["cc"] = [cc]

            built_attachments = self._build_attachments(attachments, inline_images)
            if built_attachments:
                payload["attachments"] = built_attachments

            response = requests.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if response.status_code >= 400:
                return {
                    "success": False,
                    "message": f"Erreur Resend ({response.status_code}): {response.text}"
                }

            return {
                "success": True,
                "message": f"Email envoye avec succes a {to_email}"
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "message": f"Erreur reseau lors de l'envoi via Resend: {str(e)}"
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
            <p>Ceci est un email de test envoye depuis <strong>SDP OCR Backend</strong> (via Resend).</p>
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
