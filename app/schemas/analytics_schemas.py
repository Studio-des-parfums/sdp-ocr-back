from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------------------------
# 1. Formulas Count
# ---------------------------------------------------------------------------

class FormulaCountDataPoint(BaseModel):
    period: str = Field(..., description="Période (YYYY, YYYY-MM ou YYYY-MM-DD)")
    count: int = Field(..., description="Nombre de formules créées")


class FormulaCountResponse(BaseModel):
    total: int = Field(..., description="Nombre total de formules sur la période")
    group_by: str = Field(..., description="Granularité appliquée ('day', 'month', 'year')")
    period_label: str = Field(..., description="Label de la granularité")
    data: List[FormulaCountDataPoint] = Field(..., description="Décomposition temporelle")


# ---------------------------------------------------------------------------
# 2. Best Periods
# ---------------------------------------------------------------------------

class MonthPeriodItem(BaseModel):
    month: int = Field(..., description="Numéro du mois (1-12)")
    label: str = Field(..., description="Nom du mois en français")
    count: int = Field(..., description="Nombre de formules")


class DayOfWeekPeriodItem(BaseModel):
    day: int = Field(..., description="Jour de la semaine (1=Lundi ... 7=Dimanche)")
    label: str = Field(..., description="Nom du jour en français")
    count: int = Field(..., description="Nombre de formules")


class YearPeriodItem(BaseModel):
    year: int = Field(..., description="Année")
    count: int = Field(..., description="Nombre de formules")


class BestPeriodsResponse(BaseModel):
    top_months: List[MonthPeriodItem]
    top_days_of_week: List[DayOfWeekPeriodItem]
    top_years: List[YearPeriodItem]


# ---------------------------------------------------------------------------
# 3. Top Ateliers
# ---------------------------------------------------------------------------

class TopAtelierItem(BaseModel):
    atelier_id: Optional[int] = Field(None, description="Identifiant de l'atelier")
    atelier_name: str = Field(..., description="Nom de l'atelier")
    count: int = Field(..., description="Nombre de formules associées")


# ---------------------------------------------------------------------------
# 4. Top Notes
# ---------------------------------------------------------------------------

class TopNoteItem(BaseModel):
    name: str = Field(..., description="Nom de la note / essence")
    count: int = Field(..., description="Nombre d'utilisations")


class TopNotesResponse(BaseModel):
    top_note: Optional[List[TopNoteItem]] = None
    heart_note: Optional[List[TopNoteItem]] = None
    base_note: Optional[List[TopNoteItem]] = None
    booster_note: Optional[List[TopNoteItem]] = None
    all: Optional[List[TopNoteItem]] = None


# ---------------------------------------------------------------------------
# 5. Top Options
# ---------------------------------------------------------------------------

class TopOptionItem(BaseModel):
    option_name: str = Field(..., description="Nom de l'option choisie")
    count: int = Field(..., description="Nombre de fois choisie")


# ---------------------------------------------------------------------------
# 6. Gender Distribution
# ---------------------------------------------------------------------------

class GenderDistributionResponse(BaseModel):
    male: int = Field(..., description="Nombre de clients hommes")
    female: int = Field(..., description="Nombre de clientes femmes")
    unknown: int = Field(..., description="Nombre de clients sans genre renseigné")
    total: int = Field(..., description="Nombre total de clients")
    male_pct: float = Field(..., description="Pourcentage d'hommes parmi les genres renseignés")
    female_pct: float = Field(..., description="Pourcentage de femmes parmi les genres renseignés")
    unknown_pct: float = Field(..., description="Pourcentage de clients non renseignés parmi le total")


# ---------------------------------------------------------------------------
# 7. Top Locations
# ---------------------------------------------------------------------------

class LocationCountryItem(BaseModel):
    country: str = Field(..., description="Pays")
    count: int = Field(..., description="Nombre de clients")


class LocationCityItem(BaseModel):
    city: str = Field(..., description="Ville")
    count: int = Field(..., description="Nombre de clients")


class TopLocationsResponse(BaseModel):
    top_countries: List[LocationCountryItem]
    top_cities: List[LocationCityItem]


# ---------------------------------------------------------------------------
# 8. Loyalty Rate
# ---------------------------------------------------------------------------

class LoyaltyDistributionItem(BaseModel):
    bucket: str = Field(..., description="Tranche de nombre de formules ('1', '2', '3', '4', '5+')")
    customer_count: int = Field(..., description="Nombre de clients dans cette tranche")


class NewLoyalByMonthItem(BaseModel):
    month: str = Field(..., description="Mois d'atteinte du seuil de fidélité (YYYY-MM)")
    new_loyal: int = Field(..., description="Nombre de nouveaux clients fidèles")


class LoyaltyRateResponse(BaseModel):
    total_customers_with_formula: int = Field(..., description="Nombre total de clients ayant au moins une formule")
    loyal_customers: int = Field(..., description="Nombre de clients ayant atteint le seuil de fidélité")
    loyalty_rate: float = Field(..., description="Taux de fidélité en pourcentage")
    min_formulas_threshold: int = Field(..., description="Seuil de formules pour être considéré fidèle")
    distribution: List[LoyaltyDistributionItem] = Field(..., description="Répartition par tranche de formules")
    new_loyal_by_month: List[NewLoyalByMonthItem] = Field(..., description="Évolution mensuelle des nouveaux fidèles")
