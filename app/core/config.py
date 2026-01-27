import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY")
    PROJECT_NAME: str = "SDP OCR Backend"

    # Configuration SMTP Gmail
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "SDP OCR")

    # URL du serveur pour les fichiers statiques
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")

settings = Settings()