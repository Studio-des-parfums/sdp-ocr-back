
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    BLANK_SHEET = "blank_sheet"
    STUDIO_PARFUMS = "studio_parfums"
    UNKNOWN = "unknown"


class NoteParfum(BaseModel):
    """Ligne d'essence réellement renseignée dans un tableau."""

    essence: str | None = Field(
        default=None,
        description=(
            "Nom manuscrit de l'essence, provenant exclusivement de la "
            "colonne des essences de la ligne concernée. Ne pas extraire "
            "les titres, légendes, en-têtes, unités ou dosages imprimés "
            "pour 30 ml, 50 ml ou 100 ml. Ignorer les lignes vides, les "
            "traits isolés et les cases cochées. Ne pas inventer ni "
            "compléter un nom illisible. Si la lecture est incertaine, null."
        ),
    )
    quantite_ml: str | None = Field(
        default=None,
        description=(
            "Quantité manuscrite associée à cette essence, dans la colonne "
            "de quantité de la même ligne. Ne pas utiliser la colonne TOTAL, "
            "une coche, ni les dosages indicatifs imprimés. Ne pas déduire "
            "une quantité à partir d'une autre ligne. Si absente ou "
            "illisible, null."
        ),
    )


class MistralDocumentAnnotation(BaseModel):
    """
    Schéma d'extraction pour les fiches Studio des Parfums
    et les feuilles statistiques.
    """

    document_type: DocumentType = Field(
        description=(
            "Type du document entier. studio_parfums pour une fiche "
            "individuelle de création de parfum ; blank_sheet pour une "
            "feuille de suivi statistique ; unknown si aucun type ne "
            "correspond clairement. Ne pas classifier à partir du seul "
            "logo ou d'un mot isolé."
        )
    )

    # Studio des Parfums

    identifiant: str | None = Field(
        default=None,
        description=(
            "Numéro de création visible dans la zone identifiant/numéro "
            "de création. Conserver les chiffres dans l'ordre et les zéros. "
            "Retirer uniquement les espaces OCR à l'intérieur du numéro. "
            "Format généralement de 8 à 10 chiffres commençant par 20. "
            "Ne pas compléter les chiffres manquants par déduction."
        ),
    )

    nom_parfum: str | None = Field(
        default=None,
        description=(
            "Nom personnel du parfum, uniquement si une réponse manuscrite "
            "est visible dans la zone Nom du parfum / Perfume name. "
            "Le titre imprimé LE STUDIO DES PARFUMS, ses variantes et "
            "le logo ne sont jamais une réponse. Si la zone est vide "
            "ou si le libellé est absent sans réponse identifiable, null."
        ),
    )

    genre: str | None = Field(
        default=None,
        description=(
            "Civilité explicitement cochée parmi Mr, Mme, Mlle ou Ms. "
            "Ne pas déduire la civilité du prénom. Si aucune case n'est "
            "clairement sélectionnée, null."
        ),
    )

    nom: str | None = Field(
        default=None,
        description=(
            "Nom de famille écrit dans le champ Nom / Last name. "
            "Lire les caractères visibles. Ne pas corriger automatiquement "
            "une lettre douteuse, ni reconstruire le nom à partir de "
            "l'adresse email ou du prénom. Si la lecture est incertaine, "
            "conserver uniquement ce qui peut être transcrit de manière "
            "fiable ; sinon null."
        ),
    )

    prenom: str | None = Field(
        default=None,
        description=(
            "Prénom écrit dans le champ Prénom / First name. "
            "Ne pas le déduire du nom ou de l'adresse email. "
            "Si illisible ou absent, null."
        ),
    )

    date: str | None = Field(
        default=None,
        description=(
            "Date de création de la fiche au format YYYY-MM-DD. "
            "1. Rechercher en priorité la date manuscrite dans le champ 'Date' ou 'Date de création' "
            "(en haut de fiche ou dans les coordonnées ; ne pas confondre avec Date de naissance) "
            "et la convertir au format YYYY-MM-DD (ex: 14/07/2026 -> 2026-07-14, 02/01/22 -> 2022-01-02). "
            "2. Règle essentielle : si la date n'est pas renseignée ou est illisible dans le champ date, "
            "la déduire obligatoirement à partir du numéro identifiant si celui-ci commence par la date au format YYYYMMDD "
            "(ex: identifiant 202607145 -> date 2026-07-14, identifiant 202201021 -> date 2022-01-02). "
            "3. Renvoyer null uniquement si aucune date n'est écrite et que l'identifiant ne commence pas par une date valide."
        ),
    )

    ville: str | None = Field(
        default=None,
        description=(
            "Ville écrite dans le champ Ville / City. "
            "Ne pas la déduire du pays, du code postal ou d'autres champs."
        ),
    )

    pays: str | None = Field(
        default=None,
        description=(
            "Pays écrit dans le champ Pays / Country. "
            "Ne pas le déduire de la langue ou de l'adresse email."
        ),
    )

    tel: str | None = Field(
        default=None,
        description=(
            "Numéro écrit dans le champ Téléphone / Tel / Phone. "
            "Conserver tous les chiffres lisibles dans leur ordre, "
            "ainsi que l'indicatif international visible. Les espaces "
            "de présentation peuvent être supprimés. Ne pas inventer "
            "ou remplacer un chiffre ambigu."
        ),
    )

    email: str | None = Field(
        default=None,
        description=(
            "Adresse écrite dans la zone Email. Lire la zone sur le "
            "document, pas une reconstruction à partir du nom/prénom. "
            "Les espaces manifestement ajoutés par l'OCR autour des "
            "caractères de l'adresse peuvent être supprimés. Vérifier "
            "visuellement le nom de boîte, @, les points et le domaine. "
            "Ne pas remplacer automatiquement ! par l, I par l, O par 0, "
            "ou inversement. Ne jamais inventer une extension ou un domaine. "
            "Une adresse syntaxiquement plausible n'est pas nécessairement "
            "correcte. Si un caractère essentiel demeure ambigu, null."
        ),
    )

    profession: str | None = Field(
        default=None,
        description=(
            "Profession explicitement écrite dans le champ Profession. "
            "Ne pas la déduire du contexte."
        ),
    )

    date_naissance: str | None = Field(
        default=None,
        description=(
            "Date écrite dans Date de naissance / Birthday. "
            "Ne pas la confondre avec la date de création. "
            "Si absente ou ambiguë, null."
        ),
    )

    groupe: str | None = Field(
        default=None,
        description="Nom explicitement écrit dans le champ Groupe / Group.",
    )

    notes_de_tete: list[NoteParfum] = Field(
        default_factory=list,
        description=(
            "Uniquement les ingrédients manuscrits du tableau NOTES DE TÊTE. "
            "Une ligne doit correspondre à une véritable ligne d'ingrédient. "
            "Ignorer les textes imprimés, indications de dosage, légendes, "
            "lignes vides et traits isolés. Conserver l'ordre vertical."
        ),
    )

    notes_de_coeur: list[NoteParfum] = Field(
        default_factory=list,
        description=(
            "Uniquement les ingrédients manuscrits du tableau NOTES DE CŒUR. "
            "Ignorer les dosages indicatifs imprimés en bas du tableau, "
            "les en-têtes et les lignes vides. Ne pas importer de ligne "
            "des tableaux de tête ou de fond."
        ),
    )

    notes_de_fond: list[NoteParfum] = Field(
        default_factory=list,
        description=(
            "Uniquement les ingrédients manuscrits du tableau NOTES DE FOND. "
            "Ignorer les dosages indicatifs imprimés en bas du tableau, "
            "les en-têtes et les lignes vides. Conserver l'ordre vertical."
        ),
    )

    # Feuille statistique

    month_year: str | None = Field(
        default=None,
        description=(
            "Mois et année explicitement visibles sur la feuille statistique. "
            "Ne pas les déduire du nom de fichier ou de la date du jour."
        ),
    )

    fiches_manquantes: list[str] | None = Field(
        default=None,
        description=(
            "Numéros figurant exclusivement dans la rubrique fiches "
            "manquantes. Extraire les numéros visibles, sans compléter "
            "une séquence ni inclure les doublons."
        ),
    )

    doublons: list[str] | None = Field(
        default=None,
        description=(
            "Numéros figurant exclusivement dans la rubrique doublons. "
            "Ne pas mélanger avec les fiches manquantes."
        ),
    )

    tel_list: list[str] | None = Field(
        default=None,
        description=(
            "Valeurs de téléphone figurant dans la rubrique tel de la "
            "feuille statistique. Ne pas prendre les téléphones des fiches "
            "individuelles."
        ),
    )

    mail_list: list[str] | None = Field(
        default=None,
        description=(
            "Valeurs figurant dans la rubrique mail de la feuille statistique. "
            "Conserver la lecture source ; ne pas inventer ni réparer une "
            "adresse incertaine."
        ),
    )


# Alias générique pour l'annotation du document (OpenAI / Mistral)
DocumentAnnotation = MistralDocumentAnnotation


class BlankSheetData(BaseModel):
    month_year: str | None = None
    fiches_manquantes: list[str] = Field(default_factory=list)
    doublons: list[str] = Field(default_factory=list)
    tel: list[str] = Field(default_factory=list)
    mail: list[str] = Field(default_factory=list)


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
    notes_de_tete: list[NoteParfum] = Field(default_factory=list)
    notes_de_coeur: list[NoteParfum] = Field(default_factory=list)
    notes_de_fond: list[NoteParfum] = Field(default_factory=list)


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
