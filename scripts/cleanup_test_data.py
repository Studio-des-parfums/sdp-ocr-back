#!/usr/bin/env python3
"""
Script de nettoyage des données de test créées par Bruno.
Supprime tous les enregistrements de test (sessions, devices, groupes, logs, etc.)
sans jamais toucher aux vraies données clients du Studio des Parfums.
"""

import os
import sys

import pymysql
from dotenv import load_dotenv

# Trouver le fichier .env à la racine du projet
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")

if not os.path.exists(env_path):
    print(f"❌ Fichier .env introuvable à : {env_path}")
    sys.exit(1)

load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "railway")

print("=" * 60)
print(f"🧹 NETTOYAGE DES DONNÉES DE TEST BRUNO ({DB_NAME} @ {DB_HOST})")
print("=" * 60)

try:
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )
except Exception as e:
    print(f"❌ Erreur de connexion à la base de données : {e}")
    sys.exit(1)

cur = conn.cursor()
total_deleted = 0


def run_delete(table_name, query, description):
    global total_deleted
    try:
        cur.execute(query)
        count = cur.rowcount
        total_deleted += count
        if count > 0:
            print(f"  ✅ {description} ({table_name}) : {count} supprimé(s)")
        else:
            print(f"  ℹ️  {description} ({table_name}) : aucun élément à supprimer")
    except Exception as e:
        print(f"  ⚠️  Erreur sur {table_name} : {e}")


# 1. Sessions tablette & réponses associées
run_delete(
    "session_answers",
    "DELETE FROM session_answers WHERE session_id IN ("
    "  SELECT id FROM sessions WHERE customer_email = 'bruno.session@example.com' "
    "  OR customer_name LIKE '%Bruno%' OR customer_name = 'Client Bruno'"
    ")",
    "Réponses de sessions tablette test",
)

run_delete(
    "sessions",
    "DELETE FROM sessions WHERE customer_email = 'bruno.session@example.com' "
    "OR customer_name LIKE '%Bruno%' OR customer_name = 'Client Bruno'",
    "Sessions tablette test",
)

# 2. Groupes de test & liaisons
run_delete(
    "customer_groups",
    "DELETE FROM customer_groups WHERE group_id IN ("
    "  SELECT id FROM `groups` WHERE name LIKE 'GroupeBruno%'"
    ")",
    "Liaisons clients-groupes test",
)

run_delete("groups", "DELETE FROM `groups` WHERE name LIKE 'GroupeBruno%'", "Groupes test")

# 3. Tablettes / Devices de test
run_delete(
    "devices",
    "DELETE FROM devices WHERE device_name LIKE '%Bruno%' OR device_id LIKE 'tablet-bruno%'",
    "Tablettes/Devices de test",
)

# 4. Historique de connexion de test
run_delete(
    "login_history",
    "DELETE FROM login_history WHERE logged_at >= '2026-10-16' AND id >= 60",
    "Logs de connexion test",
)

# 5. Clients de test (si non supprimés par leur requête DELETE)
run_delete(
    "customers",
    "DELETE FROM customers WHERE (first_name LIKE '%Bruno%' OR last_name LIKE '%Bruno%') "
    "AND email LIKE '%@example.com%'",
    "Clients de test orphelins",
)

# 6. Commandes & items de test
run_delete(
    "order_items",
    "DELETE FROM order_items WHERE order_id IN ("
    "  SELECT id FROM orders WHERE comment LIKE '%Bruno%'"
    ")",
    "Items de commande test",
)

run_delete("orders", "DELETE FROM orders WHERE comment LIKE '%Bruno%'", "Commandes test orphelines")

# 7. Utilisateurs de test
run_delete(
    "users",
    "DELETE FROM users WHERE email LIKE '%bruno%@example.com'",
    "Utilisateurs test orphelins",
)

# 8. Rôles de test
run_delete("roles", "DELETE FROM roles WHERE name LIKE '%Bruno%'", "Rôles test orphelins")

# 9. Avis clients / Customer Reviews de test
run_delete(
    "customers_review",
    "DELETE FROM customers_review WHERE email LIKE '%bruno%@example.com' OR first_name LIKE '%Bruno%'",
    "Avis clients de test orphelins",
)

conn.close()

print("-" * 60)
print(f"🎉 Nettoyage terminé avec succès ! ({total_deleted} enregistrement(s) supprimé(s))")
print("=" * 60)
