from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.repositories.analytics_repository import analytics_repository
from app.schemas.analytics_schemas import (
    BestPeriodsResponse,
    FormulaCountResponse,
    GenderDistributionResponse,
    LoyaltyRateResponse,
    TopAtelierItem,
    TopLocationsResponse,
    TopNotesResponse,
    TopOptionItem,
)

router = APIRouter()


def _validate_date(date_str: str | None, param_name: str) -> str | None:
    """Valide qu'une chaîne de date correspond au format YYYY-MM-DD."""
    if not date_str:
        return None
    cleaned = date_str.strip()
    try:
        datetime.strptime(cleaned, "%Y-%m-%d")
        return cleaned
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Format de date invalide pour {param_name} : '{date_str}'. Format attendu : YYYY-MM-DD",
        )


def _validate_date_range(
    date_from: str | None, date_to: str | None
) -> tuple[str | None, str | None]:
    """Valide les dates de début et fin ainsi que leur cohérence chronologique."""
    d_from = _validate_date(date_from, "date_from")
    d_to = _validate_date(date_to, "date_to")
    if d_from and d_to and d_from > d_to:
        raise HTTPException(
            status_code=400, detail="date_from doit être antérieure ou égale à date_to"
        )
    return d_from, d_to


# ---------------------------------------------------------------------------
# 1. Nb de formules total en fonction d'une date
# ---------------------------------------------------------------------------


@router.get(
    "/formulas/count", response_model=FormulaCountResponse, summary="Nombre de formules par période"
)
async def formula_count_by_date(
    date_from: str | None = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Date de fin (YYYY-MM-DD)"),
    group_by: str = Query("month", description="Granularité : 'day' | 'month' | 'year'"),
):
    """
    Retourne le nombre total de formules créées (avec filtre de dates optionnel)
    et la décomposition temporelle selon la granularité choisie.
    """
    clean_group_by = group_by.strip().lower()
    if clean_group_by not in ("day", "month", "year"):
        raise HTTPException(status_code=400, detail="group_by doit être 'day', 'month' ou 'year'")

    d_from, d_to = _validate_date_range(date_from, date_to)

    try:
        return analytics_repository.get_formula_count_by_date(
            date_from=d_from,
            date_to=d_to,
            group_by=clean_group_by,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics formulas/count : {e}")


# ---------------------------------------------------------------------------
# 2. Meilleurs mois / jours de l'année
# ---------------------------------------------------------------------------


@router.get(
    "/formulas/best-periods",
    response_model=BestPeriodsResponse,
    summary="Meilleurs mois et jours de l'année",
)
async def best_periods(
    limit: int = Query(10, ge=1, le=50, description="Nombre max de résultats par catégorie"),
):
    """
    Classement des mois (1-12), jours de la semaine (Lundi-Dimanche)
    et années qui concentrent le plus de formules créées.
    """
    try:
        return analytics_repository.get_best_periods(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics formulas/best-periods : {e}")


# ---------------------------------------------------------------------------
# 3. Classement des ateliers
# ---------------------------------------------------------------------------


@router.get(
    "/ateliers/top", response_model=list[TopAtelierItem], summary="Ateliers les plus fréquentés"
)
async def top_ateliers(
    limit: int = Query(10, ge=1, le=50, description="Nombre max de résultats"),
    date_from: str | None = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Date de fin (YYYY-MM-DD)"),
):
    """
    Classement des ateliers par nombre de formules associées.
    """
    d_from, d_to = _validate_date_range(date_from, date_to)
    try:
        return analytics_repository.get_top_ateliers(limit=limit, date_from=d_from, date_to=d_to)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics ateliers/top : {e}")


# ---------------------------------------------------------------------------
# 4. Classement des notes les plus utilisées
# ---------------------------------------------------------------------------


@router.get(
    "/notes/top",
    response_model=TopNotesResponse,
    response_model_exclude_none=True,
    summary="Notes les plus utilisées",
)
async def top_notes(
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats par type"),
    note_type: str | None = Query(
        None,
        description="Type de note : 'top_note' | 'heart_note' | 'base_note' | 'booster_note'. Vide = toutes.",
    ),
    date_from: str | None = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Date de fin (YYYY-MM-DD)"),
):
    """
    Classement des essences (notes) les plus utilisées dans les formules.
    Retourne un objet avec une clé par type de note + une clé `all` pour le top global.
    Exclut automatiquement les placeholders non définis ('A définir').
    """
    valid_types = {"top_note", "heart_note", "base_note", "booster_note"}
    clean_note_type = note_type.strip().lower() if note_type else None
    if clean_note_type and clean_note_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"note_type invalide. Valeurs acceptées : {', '.join(sorted(valid_types))}",
        )

    d_from, d_to = _validate_date_range(date_from, date_to)
    try:
        return analytics_repository.get_top_notes(
            limit=limit,
            note_type=clean_note_type,
            date_from=d_from,
            date_to=d_to,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics notes/top : {e}")


# ---------------------------------------------------------------------------
# 5. Classement des options les plus choisies
# ---------------------------------------------------------------------------


@router.get("/options/top", response_model=list[TopOptionItem], summary="Options les plus choisies")
async def top_options(
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats"),
    date_from: str | None = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Date de fin (YYYY-MM-DD)"),
):
    """
    Classement des options (quantité, coffret, extras…) les plus souvent
    choisies dans les formules.
    """
    d_from, d_to = _validate_date_range(date_from, date_to)
    try:
        return analytics_repository.get_top_options(limit=limit, date_from=d_from, date_to=d_to)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics options/top : {e}")


# ---------------------------------------------------------------------------
# 6. Répartition Homme / Femme
# ---------------------------------------------------------------------------


@router.get(
    "/customers/gender",
    response_model=GenderDistributionResponse,
    summary="Répartition Homme / Femme",
)
async def gender_distribution(
    date_from: str | None = Query(None, description="Date de début inscription (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Date de fin inscription (YYYY-MM-DD)"),
):
    """
    Pourcentage et compteurs de clients Homme / Femme / Non renseigné parmi tous les clients.
    Le filtre date porte sur la date d'inscription (created_at).
    """
    d_from, d_to = _validate_date_range(date_from, date_to)
    try:
        return analytics_repository.get_gender_distribution(date_from=d_from, date_to=d_to)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics customers/gender : {e}")


# ---------------------------------------------------------------------------
# 7. Classement clients par ville / pays
# ---------------------------------------------------------------------------


@router.get(
    "/customers/locations",
    response_model=TopLocationsResponse,
    summary="Classement clients par ville et pays",
)
async def top_locations(
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats"),
    date_from: str | None = Query(None, description="Date de début inscription (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Date de fin inscription (YYYY-MM-DD)"),
):
    """
    Top villes et top pays selon le nombre de clients inscrits.
    """
    d_from, d_to = _validate_date_range(date_from, date_to)
    try:
        return analytics_repository.get_top_locations(limit=limit, date_from=d_from, date_to=d_to)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics customers/locations : {e}")


# ---------------------------------------------------------------------------
# 8. Taux de fidélité
# ---------------------------------------------------------------------------


@router.get("/customers/loyalty", response_model=LoyaltyRateResponse, summary="Taux de fidélité")
async def loyalty_rate(
    min_formulas: int = Query(2, ge=2, description="Seuil de formules pour être considéré fidèle"),
    date_from: str | None = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Date de fin (YYYY-MM-DD)"),
):
    """
    Taux de fidélité des clients :
    - Clients fidèles = ceux ayant au moins `min_formulas` formules sur la période
    - Distribution par tranche de nombre de formules (1, 2, 3, 4, 5+)
    - Évolution mensuelle des nouveaux clients atteignant le seuil de fidélité
    """
    d_from, d_to = _validate_date_range(date_from, date_to)
    try:
        return analytics_repository.get_loyalty_rate(
            min_formulas=min_formulas,
            date_from=d_from,
            date_to=d_to,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics customers/loyalty : {e}")
