SDP OCR Backend
Backend FastAPI pour l’extraction OCR de formulaires PDF du Studio des Parfums, l’enrichissement métier des données, leur persistance en base MySQL, la gestion documentaire associée, et les opérations annexes autour des clients, groupes, commandes, formules et emails.

Fonctionnalités
OCR de fichiers PDF via Mistral OCR
Découpage automatique des PDF page par page
Classification des documents :
studio_parfums
blank_sheet
unknown
Extraction structurée des champs clients depuis les formulaires
Extraction des notes olfactives depuis les tableaux OCR
Validation et normalisation métier :
correction de domaines email
vérification DNS/MX des domaines email
validation d’email via API externe
normalisation et validation des numéros de téléphone
correction de pays / ville
détection de doublons
Insertion automatique en base :
customers
customer_reviews si anomalie ou doublon
formula, top_note, heart_note, base_note
rattachement aux groupes
Stockage des PDF et images générées :
local
S3 / R2 compatible
API métier complète pour :
clients
customer reviews
groupes
utilisateurs
rôles
commandes
fichiers
formules
export CSV
envoi d’emails
Stack technique
Python
FastAPI
Uvicorn
MySQL avec pool de connexions DBUtils
Mistral OCR API
PyPDF2 pour le split PDF
pdf2image + Pillow pour générer les images
boto3 pour le stockage objet
dnspython pour la validation MX
WeasyPrint présent dans les dépendances
SMTP Gmail pour l’envoi d’emails
Arborescence principale
app/
  api/endpoints/        # Routes FastAPI
  core/                 # Config, logs, client Mistral
  database/             # Connexion MySQL
  repositories/         # Accès aux données
  services/             # Logique métier
  schemas/              # Modèles Pydantic
  utils/                # OCR helpers, extraction, split PDF, CSV...
files/                  # Stockage local des fichiers
tests/                  # Scripts/tests utilitaires
run.py                  # Point d’entrée local / Render
Procfile                # Déploiement Render
Installation
1. Cloner le projet
git clone <url-du-repo>
cd sdp-ocr-back
2. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate
3. Installer les dépendances Python
pip install -r requirements.txt
4. Installer les dépendances système
Selon l’OS, certaines librairies peuvent être nécessaires :

pdf2image requiert généralement Poppler
WeasyPrint peut nécessiter ses dépendances natives (Cairo / Pango selon l’environnement)
Exemple macOS :

brew install poppler
Variables d’environnement
Créer un fichier .env à la racine :

MISTRAL_API_KEY=
DB_HOST=localhost
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=SDP OCR
SMTP_CC_EMAIL=

SERVER_URL=http://localhost:8000

STORAGE_BACKEND=local
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_S3_REGION=us-east-1
AWS_S3_ENDPOINT=

ABSTRACT_API_KEY=
Variables importantes
MISTRAL_API_KEY : obligatoire pour l’OCR
DB_* : obligatoire pour la base MySQL
SMTP_* : nécessaires pour les endpoints email
ABSTRACT_API_KEY : utilisé pour la validation email
STORAGE_BACKEND=local|s3 : choix du backend de stockage
Lancement du projet
En local
python run.py
Ou :

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Accès
API : http://localhost:8000
Swagger : http://localhost:8000/docs
Healthcheck : http://localhost:8000/health
Déploiement
Le projet est configuré pour Render avec :

web: python run.py
Flux OCR
Upload d’un PDF
Découpage du PDF en pages unitaires
Tentative d’extraction structurée via document_annotation
Fallback OCR texte si nécessaire
Classification du document
Extraction des champs métier
Extraction des notes olfactives depuis les tableaux
Validation / correction des données
Insertion en base
Sauvegarde du PDF et des images associées
Création éventuelle de formule et affectation à un groupe
Endpoints principaux
OCR
POST /api/v1/ocr/upload-pdf : OCR synchrone avec retour JSON détaillé
POST /api/v1/ocr/upload-pdf-csv : création d’un job asynchrone
GET /api/v1/ocr/jobs/{job_id} : statut d’un job OCR
GET /api/v1/ocr/jobs : liste des jobs
GET /api/v1/ocr/health : healthcheck OCR
Clients / Reviews
GET /api/v1/customers
POST /api/v1/customers
PUT /api/v1/customers/{id}
PUT /api/v1/customers/bulk
GET /api/v1/customer-reviews
POST /api/v1/customer-reviews
POST /api/v1/customer-reviews/{id}/transfer
Fichiers / Formules
GET /api/v1/customers/{customer_id}/files
GET /api/v1/files/{file_id}/content
GET /api/v1/formulas/{formula_id}
PUT /api/v1/formulas/{formula_id}/notes
Groupes / Utilisateurs / Commandes
CRUD groupes, rôles, utilisateurs, commandes
gestion des quotas utilisateur
fusion et restauration de groupes
affectation de clients à des groupes
notification email sur attribution de commandes
Export / Email
POST /api/v1/export/generate-csv
POST /api/v1/emails/test
POST /api/v1/emails/pyramid/preview
POST /api/v1/emails/pyramid
Tests
Le dossier tests/ contient surtout des scripts de validation ciblés :

test de connexion MySQL
validation de domaines email
correction automatique d’emails
logique fuzzy sur les notes
Exécution :

pytest
Selon la configuration locale, certains tests peuvent dépendre :

d’un accès réseau
d’une base MySQL disponible
de clés API actives

Licence
Projet privé / usage interne, à préciser selon votre contexte.
