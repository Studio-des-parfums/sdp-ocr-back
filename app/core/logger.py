import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = "logs"


def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Éviter les doublons si setup_logging() est appelé plusieurs fois
    if root_logger.handlers:
        return

    # Console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Fichier principal (rotation quotidienne, 30 jours)
    file_handler = TimedRotatingFileHandler(
        os.path.join(LOGS_DIR, "app.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Fichier erreurs uniquement
    error_handler = TimedRotatingFileHandler(
        os.path.join(LOGS_DIR, "errors.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.error").propagate = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
