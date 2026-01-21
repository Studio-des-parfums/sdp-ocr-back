import os

import pymysql
from pymysql import MySQLError
from dotenv import load_dotenv


# Charge les variables d'environnement depuis le fichier .env (si présent)
load_dotenv()


def get_connection():
    """
    Crée une connexion MySQL en utilisant les variables d'environnement suivantes :
    - DB_HOST
    - DB_PORT
    - DB_USER
    - DB_PASSWORD
    - DB_NAME
    """
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

        print("Connexion MySQL réussie (PyMySQL)")
        return connection

    except MySQLError as e:
        print(f"Erreur de connexion MySQL : {e}")
        return None
