import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY")
    PROJECT_NAME: str = "SDP OCR Backend"

    # OpenAI (répartition intelligente des quantités de notes olfactives)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Dashboard SDP (règles de dosage max par ingrédient/coffret/flacon)
    DASHBOARD_API_URL: str = os.getenv(
        "DASHBOARD_API_URL", "https://sdp-dashboard-back-production.up.railway.app"
    )

    # Configuration Resend (envoi d'emails via API HTTP)
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "")
    RESEND_FROM_NAME: str = os.getenv("RESEND_FROM_NAME", "Le Studio des Parfums")
    EMAIL_CC_ADDRESS: str = os.getenv("EMAIL_CC_ADDRESS", "")

    # URL du serveur pour les fichiers statiques
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")

    # Stockage fichiers : "local" ou "s3"
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    AWS_S3_REGION: str = os.getenv("AWS_S3_REGION", "us-east-1")
    AWS_S3_ENDPOINT: str = os.getenv("AWS_S3_ENDPOINT", "")  # laisser vide pour AWS natif

settings = Settings()