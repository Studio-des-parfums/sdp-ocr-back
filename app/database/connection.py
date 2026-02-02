import os

import pymysql
from pymysql import MySQLError
from dbutils.pooled_db import PooledDB
from dotenv import load_dotenv


# Charge les variables d'environnement depuis le fichier .env (si présent)
load_dotenv()

# Pool de connexions global (singleton)
_connection_pool = None


def _get_pool():
    """
    Retourne le pool de connexions (le crée si nécessaire).
    Le pool réutilise les connexions existantes au lieu d'en créer de nouvelles.
    """
    global _connection_pool

    if _connection_pool is None:
        try:
            _connection_pool = PooledDB(
                creator=pymysql,
                maxconnections=10,  # Max connexions dans le pool
                mincached=2,        # Connexions min gardées en cache
                maxcached=5,        # Connexions max gardées en cache
                blocking=True,      # Attendre si le pool est plein
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
            print("Pool de connexions MySQL initialisé")
        except MySQLError as e:
            print(f"Erreur création pool MySQL : {e}")
            return None

    return _connection_pool


def get_connection():
    """
    Récupère une connexion depuis le pool.
    La connexion est automatiquement retournée au pool quand elle est fermée.
    """
    try:
        pool = _get_pool()
        if pool is None:
            return None

        connection = pool.connection()
        return connection

    except MySQLError as e:
        print(f"Erreur de connexion MySQL : {e}")
        return None
