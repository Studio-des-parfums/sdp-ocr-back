from typing import Dict, Any, List, Optional

from app.database import get_connection
from app.crud import crud_formula, crud_notes
from app.utils.note_corrector import note_corrector


class FormulaRepository:
    """
    Repository pour gérer les formules et leurs notes associées.
    """

    def create_formula_with_notes(
        self,
        customer_id: Optional[int],
        file_id: int,
        extracted_data: Dict[str, Any],
        customer_review_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Crée une formule liée à un customer (optionnel) et à un fichier,
        puis insère les notes de tête / cœur / fond associées.

        Args:
            customer_id: ID du customer ou None (pour customers_review)
            file_id: ID du fichier source (customer_files.id)
            extracted_data: Données extraites de l'OCR, incluant
                            éventuellement notes_de_tete, notes_de_coeur,
                            notes_de_fond.
            customer_review_id: ID du customer_review (optionnel)

        Returns:
            ID de la formule créée ou None si erreur
        """
        connection = get_connection()
        if not connection:
            return None

        try:
            formula_id = crud_formula.create(
                connection, customer_id, file_id, customer_review_id=customer_review_id
            )
            if not formula_id:
                return None

            def _normalize_notes(key: str) -> List[Dict[str, Any]]:
                raw_notes = extracted_data.get(key) or []
                if not isinstance(raw_notes, list):
                    return []
                normalized: List[Dict[str, Any]] = []
                for note in raw_notes:
                    if not isinstance(note, dict):
                        continue
                    name = (note.get("essence") or "").strip()
                    if not name or name == "---":
                        continue
                    
                    # Correction du nom via Fuzzy Matching
                    corrected_name = note_corrector.correct_note_name(name)
                    
                    quantity_raw = note.get("quantite_ml")
                    quantity = None
                    if quantity_raw is not None:
                        quantity = str(quantity_raw).strip()
                    normalized.append({"name": corrected_name, "quantity": quantity})
                return normalized

            top_notes = _normalize_notes("notes_de_tete")
            heart_notes = _normalize_notes("notes_de_coeur")
            base_notes = _normalize_notes("notes_de_fond")

            for note in top_notes:
                crud_notes.create_top_note(
                    connection,
                    formula_id,
                    note["name"],
                    note.get("quantity"),
                )

            for note in heart_notes:
                crud_notes.create_heart_note(
                    connection,
                    formula_id,
                    note["name"],
                    note.get("quantity"),
                )

            for note in base_notes:
                crud_notes.create_base_note(
                    connection,
                    formula_id,
                    note["name"],
                    note.get("quantity"),
                )

            return formula_id

        finally:
            if connection.open:
                connection.close()


formula_repository = FormulaRepository()

