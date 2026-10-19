from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    BLANK_SHEET = "blank_sheet"
    STUDIO_PARFUMS = "studio_parfums"
    UNKNOWN = "unknown"


class MistralDocumentAnnotation(BaseModel):
    """
    Schéma utilisé par Mistral Document AI (Annotations) pour renvoyer un JSON structuré.
    On garde un schéma "large" (champs optionnels) pour couvrir les 2 types de documents.

    Les descriptions Field() servent d'instructions à Mistral pour mieux identifier les champs.
    """

    document_type: DocumentType | None = Field(
        None,
        description="Type de document détecté: 'studio_parfums' (formulaire Studio des Parfums), 'blank_sheet' (feuille blanche avec statistiques), ou 'unknown'",
    )

    # Studio des Parfums
    identifiant: str | None = Field(
        None,
        description="Identifiant unique en haut de page (8 à 10 chiffres, commence toujours par '20'). Exemple: '202201008' ou '20201008'. Peut être écrit avec des espaces dans l'OCR comme '2022 01008'.",
    )
    nom_parfum: str | None = Field(
        None,
        description="Nom donné au parfum créé, écrit à la main par le client après un label du type 'Nom du parfum', 'Nom parfum' (français) ou 'Perfume name' (anglais), généralement en haut de la fiche à côté du numéro de création. Selon le modèle de fiche, ce label peut être absent. C'est un champ souvent laissé vide : ne jamais renvoyer 'LE STUDIO DES PARFUMS', 'Studio des Parfums' ou 'The Studio des Parfums' (c'est le titre imprimé de l'en-tête, pas une réponse du client). Si rien n'est écrit après le label, ou si le label est absent, renvoyer null.",
    )
    genre: str | None = Field(
        None,
        description="Genre de la personne: 'Mr', 'Mme', 'Mlle' ou 'Ms'. Chercher les cases cochées (☑, ✓, [x]) à côté de ces mentions.",
    )
    nom: str | None = Field(
        None,
        description="Nom de famille de la personne. Chercher après 'Nom:', 'Last name:' ou 'Name:'",
    )
    prenom: str | None = Field(
        None, description="Prénom de la personne. Chercher après 'Prénom:' ou 'First name:'"
    )
    date: str | None = Field(
        None,
        description="Date (généralement la date de remplissage du formulaire). Chercher après 'Date:'",
    )
    ville: str | None = Field(
        None, description="Ville de résidence. Chercher après 'Ville:' ou 'City:'"
    )
    pays: str | None = Field(
        None, description="Pays de résidence. Chercher après 'Pays:' ou 'Country:'"
    )
    tel: str | None = Field(
        None, description="Numéro de téléphone. Chercher après 'Tel:', 'Phone:' ou 'Tel:'"
    )
    email: str | None = Field(None, description="Adresse email. Chercher après 'Email:'")
    profession: str | None = Field(
        None, description="Profession de la personne. Chercher après 'Profession:'"
    )
    date_naissance: str | None = Field(
        None,
        description="Date de naissance. Chercher après 'Date de naissance:', 'Date naissance:' ou 'Birthday:'",
    )
    groupe: str | None = Field(
        None, description="Nom du groupe de la personne. Chercher après 'Groupe:' ou 'Group:'"
    )

    # Blank sheet
    month_year: str | None = Field(
        None,
        description="Mois et année de la feuille blanche (ex: 'janvier 2024' ou '01/2024'). Généralement en haut de la page.",
    )
    fiches_manquantes: list[str] | None = Field(
        None,
        description="Liste des numéros de fiches manquantes. Chercher après 'fiches manquantes:' ou 'fiches manquantes' et extraire tous les numéros qui suivent.",
    )
    doublons: list[str] | None = Field(
        None,
        description="Liste des numéros de doublons détectés. Chercher après 'doublons:' ou 'doublons' et extraire tous les numéros qui suivent.",
    )
    tel_list: list[str] | None = Field(
        None,
        description="Liste des numéros de téléphone avec problèmes. Chercher après 'tel:' et extraire tous les numéros qui suivent.",
    )
    mail_list: list[str] | None = Field(
        None,
        description="Liste des emails avec problèmes. Chercher après 'mail:' et extraire tous les emails/numéros qui suivent.",
    )


class BlankSheetData(BaseModel):
    month_year: str | None = None
    fiches_manquantes: list[str] = []
    doublons: list[str] = []
    tel: list[str] = []
    mail: list[str] = []


class StudioParfumsData(BaseModel):
    title_detected: bool = False
    identifiant: str | None = None
    nom_parfum: str | None = None
    genre: str | None = None
    nom: str | None = None
    prenom: str | None = None
    date: str | None = None
    ville: str | None = None
    pays: str | None = None
    tel: str | None = None
    email: str | None = None
    profession: str | None = None
    date_naissance: str | None = None
    groupe: str | None = None


class ProcessedPage(BaseModel):
    page_number: int
    document_type: DocumentType
    confidence: float
    raw_text: str
    extracted_data: dict[str, Any]


class OCRResponse(BaseModel):
    success: bool
    filename: str
    total_pages: int
    processed_pages: list[ProcessedPage]
    summary: dict[str, Any]
