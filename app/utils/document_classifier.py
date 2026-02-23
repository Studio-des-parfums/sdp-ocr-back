import re
from typing import Tuple
from app.schemas.ocr_schemas import DocumentType

class DocumentClassifier:
    def __init__(self):
        # Mots-clés principaux (mention exacte du studio)
        self.studio_parfums_keywords = [
            "LE STUDIO DES PARFUMS",
            "STUDIO DES PARFUMS",
            "STUDIO PARFUMS"
        ]

        # Indicateurs spécifiques au formulaire parfumeur (résistants aux fautes OCR)
        self.studio_parfums_indicators = [
            "notes de tête",
            "notes de tete",
            "notes de coeur",
            "notes de cœur",
            "notes de fond",
            "votre parfum",
            "date de naissance",
            "origine contact",
            "rgpd",
        ]

        # Mots-clés spécifiques aux feuilles de statistiques (pas présents dans les formulaires)
        self.blank_sheet_keywords = [
            "fiches manquantes",
            "doublons",
        ]

    def classify_document(self, text: str) -> Tuple[DocumentType, float]:
        """
        Classify document based on extracted text
        Returns: (DocumentType, confidence_score)
        """
        text_lower = text.lower()

        # Check for Studio des Parfums
        studio_score = self._calculate_studio_score(text_lower)

        # Check for blank sheet indicators
        blank_score = self._calculate_blank_sheet_score(text_lower)

        # Determine document type based on scores
        if studio_score > blank_score and studio_score > 0.3:
            return DocumentType.STUDIO_PARFUMS, studio_score
        elif blank_score > studio_score and blank_score > 0.3:
            return DocumentType.BLANK_SHEET, blank_score
        else:
            return DocumentType.UNKNOWN, max(studio_score, blank_score)

    def _calculate_studio_score(self, text: str) -> float:
        """Calculate confidence score for Studio des Parfums document"""
        score = 0.0

        # Keyword principal (+0.8 si présent)
        for keyword in self.studio_parfums_keywords:
            if keyword.lower() in text:
                score += 0.8
                break

        # Indicateurs spécifiques au formulaire (+0.2 chacun, max 0.6)
        indicator_score = 0.0
        for indicator in self.studio_parfums_indicators:
            if indicator in text:
                indicator_score += 0.2
        score += min(indicator_score, 0.6)

        return min(score, 1.0)

    def _calculate_blank_sheet_score(self, text: str) -> float:
        """Calculate confidence score for blank sheet document"""
        score = 0.0
        found_keywords = 0

        for keyword in self.blank_sheet_keywords:
            if keyword in text:
                found_keywords += 1
                score += 0.4

        # Mois en toutes lettres + année (ex: "janvier 2024") — spécifique aux feuilles de stats
        month_pattern = r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b'
        if re.search(month_pattern, text, re.IGNORECASE):
            score += 0.3

        # Bonus si les deux mots-clés sont présents
        if found_keywords >= 2:
            score += 0.2

        return min(score, 1.0)

document_classifier = DocumentClassifier()