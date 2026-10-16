from typing import Any, Dict, List, Optional

from app.database import get_connection
from app.crud import crud_analytics


class AnalyticsRepository:
    """
    Repository pour les routes d'analyse avancée.
    Toutes les méthodes ouvrent leur propre connexion et la ferment en fin d'appel.
    """

    # ------------------------------------------------------------------
    # 1. Nb de formules en fonction d'une plage de dates
    # ------------------------------------------------------------------

    def get_formula_count_by_date(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        group_by: str = "month",
    ) -> Dict[str, Any]:
        """
        Nombre de formules créées, avec décomposition temporelle.

        Args:
            date_from: Date de début (YYYY-MM-DD)
            date_to:   Date de fin   (YYYY-MM-DD)
            group_by:  'day' | 'month' | 'year'
        """
        connection = get_connection()
        if not connection:
            return {"total": 0, "group_by": group_by, "period_label": group_by, "data": []}
        try:
            return crud_analytics.get_formula_count_by_date(connection, date_from, date_to, group_by)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # 2. Meilleurs mois / jours de l'année
    # ------------------------------------------------------------------

    def get_best_periods(self, limit: int = 10) -> Dict[str, Any]:
        """
        Classement des mois, jours de la semaine et années par nombre de formules.
        """
        connection = get_connection()
        if not connection:
            return {"top_months": [], "top_days_of_week": [], "top_years": []}
        try:
            return crud_analytics.get_best_periods(connection, limit=limit)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # 3. Classement des ateliers
    # ------------------------------------------------------------------

    def get_top_ateliers(
        self,
        limit: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Ateliers les plus fréquentés (par nombre de formules)."""
        connection = get_connection()
        if not connection:
            return []
        try:
            return crud_analytics.get_top_ateliers(connection, limit=limit, date_from=date_from, date_to=date_to)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # 4. Classement des notes
    # ------------------------------------------------------------------

    def get_top_notes(
        self,
        limit: int = 20,
        note_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Notes (essences) les plus utilisées.

        Args:
            note_type: 'top_note'|'heart_note'|'base_note'|'booster_note'|None (=toutes)
        """
        connection = get_connection()
        if not connection:
            return {}
        try:
            return crud_analytics.get_top_notes(connection, limit=limit, note_type=note_type,
                                                 date_from=date_from, date_to=date_to)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # 5. Classement des options
    # ------------------------------------------------------------------

    def get_top_options(
        self,
        limit: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Options les plus choisies."""
        connection = get_connection()
        if not connection:
            return []
        try:
            return crud_analytics.get_top_options(connection, limit=limit, date_from=date_from, date_to=date_to)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # 6. Répartition Homme / Femme
    # ------------------------------------------------------------------

    def get_gender_distribution(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pourcentage clients Homme / Femme / Non renseigné."""
        connection = get_connection()
        if not connection:
            return {"male": 0, "female": 0, "unknown": 0, "total": 0, "male_pct": 0.0, "female_pct": 0.0, "unknown_pct": 0.0}
        try:
            return crud_analytics.get_gender_distribution(connection, date_from=date_from, date_to=date_to)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # 7. Classement par ville / pays
    # ------------------------------------------------------------------

    def get_top_locations(
        self,
        limit: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Classement des villes et pays par nombre de clients."""
        connection = get_connection()
        if not connection:
            return {"top_countries": [], "top_cities": []}
        try:
            return crud_analytics.get_top_locations(connection, limit=limit, date_from=date_from, date_to=date_to)
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # 8. Taux de fidélité
    # ------------------------------------------------------------------

    def get_loyalty_rate(
        self,
        min_formulas: int = 2,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Taux de fidélité des clients.

        Args:
            min_formulas: Seuil de formules pour être considéré fidèle (défaut 2)
        """
        connection = get_connection()
        if not connection:
            return {
                "total_customers_with_formula": 0,
                "loyal_customers": 0,
                "loyalty_rate": 0,
                "min_formulas_threshold": min_formulas,
                "distribution": [],
                "new_loyal_by_month": [],
            }
        try:
            return crud_analytics.get_loyalty_rate(connection, min_formulas=min_formulas,
                                                    date_from=date_from, date_to=date_to)
        finally:
            connection.close()


analytics_repository = AnalyticsRepository()
