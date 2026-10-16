from typing import Any, Dict, List, Optional
import pymysql

from app.core.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# 1. Nb de formules total en fonction d'une date
# ---------------------------------------------------------------------------

def get_formula_count_by_date(
    connection: pymysql.connections.Connection,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    group_by: str = "month",  # "day" | "month" | "year"
) -> Dict[str, Any]:
    """
    Retourne le nombre total de formules créées, avec une décomposition
    temporelle (par jour, mois ou année) selon le filtre de dates.

    Args:
        connection: Connexion MySQL
        date_from: Date de début (YYYY-MM-DD), incluse
        date_to:   Date de fin   (YYYY-MM-DD), incluse
        group_by:  Granularité du regroupement temporel ('day'|'month'|'year')

    Returns:
        Dict avec total global et liste de {period, count}
    """
    cursor = None
    try:
        cursor = connection.cursor()

        conditions = ["f.customer_id IS NOT NULL", "f.created_at IS NOT NULL"]
        params: List[Any] = []

        if date_from:
            conditions.append("DATE(f.created_at) >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("DATE(f.created_at) <= %s")
            params.append(date_to)

        where_clause = "WHERE " + " AND ".join(conditions)

        # Total global
        cursor.execute(f"SELECT COUNT(*) AS total FROM formula f {where_clause}", params)
        total = (cursor.fetchone() or {}).get("total", 0)

        # Regroupement temporel
        if group_by == "day":
            period_expr = "DATE_FORMAT(f.created_at, '%%Y-%%m-%%d')"
            period_label = "date"
        elif group_by == "year":
            period_expr = "DATE_FORMAT(f.created_at, '%%Y')"
            period_label = "year"
        else:  # month (default)
            period_expr = "DATE_FORMAT(f.created_at, '%%Y-%%m')"
            period_label = "month"

        group_query = f"""
            SELECT {period_expr} AS period, COUNT(*) AS count
            FROM formula f
            {where_clause}
            GROUP BY period
            ORDER BY period ASC
        """
        cursor.execute(group_query, params)
        by_period = cursor.fetchall() or []

        return {
            "total": total,
            "group_by": group_by,
            "period_label": period_label,
            "data": [{"period": str(row["period"]), "count": row["count"]} for row in by_period],
        }

    except Exception as e:
        logger.error(f"Erreur get_formula_count_by_date : {e}", exc_info=True)
        return {"total": 0, "group_by": group_by, "period_label": group_by, "data": []}
    finally:
        if cursor:
            cursor.close()


# ---------------------------------------------------------------------------
# 2. Classement des meilleurs mois / jours de l'année
# ---------------------------------------------------------------------------

def get_best_periods(
    connection: pymysql.connections.Connection,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Retourne les mois, jours de la semaine (1=Lundi…7=Dimanche) et années
    qui concentrent le plus de formules créées, toutes années confondues.

    Returns:
        Dict avec top_months, top_days_of_week et top_years
    """
    cursor = None
    try:
        cursor = connection.cursor()

        # Top mois (1=Janvier…12=Décembre)
        cursor.execute("""
            SELECT MONTH(created_at) AS month, COUNT(*) AS count
            FROM formula
            WHERE customer_id IS NOT NULL AND created_at IS NOT NULL
            GROUP BY month
            ORDER BY count DESC
            LIMIT %s
        """, (limit,))
        top_months = cursor.fetchall() or []

        # Top jours de la semaine (1=Lundi…7=Dimanche avec DAYOFWEEK MySQL : 1=Dim, 2=Lun…)
        cursor.execute("""
            SELECT
                CASE DAYOFWEEK(created_at)
                    WHEN 1 THEN 7
                    ELSE DAYOFWEEK(created_at) - 1
                END AS day_of_week,
                COUNT(*) AS count
            FROM formula
            WHERE customer_id IS NOT NULL AND created_at IS NOT NULL
            GROUP BY day_of_week
            ORDER BY count DESC
            LIMIT %s
        """, (limit,))
        top_days = cursor.fetchall() or []

        # Top années
        cursor.execute("""
            SELECT YEAR(created_at) AS year, COUNT(*) AS count
            FROM formula
            WHERE customer_id IS NOT NULL AND created_at IS NOT NULL
            GROUP BY year
            ORDER BY count DESC
            LIMIT %s
        """, (limit,))
        top_years = cursor.fetchall() or []

        day_names = {1: "Lundi", 2: "Mardi", 3: "Mercredi", 4: "Jeudi",
                     5: "Vendredi", 6: "Samedi", 7: "Dimanche"}
        month_names = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                       5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                       9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"}

        return {
            "top_months": [
                {"month": r["month"], "label": month_names.get(r["month"], str(r["month"])), "count": r["count"]}
                for r in top_months
            ],
            "top_days_of_week": [
                {"day": r["day_of_week"], "label": day_names.get(r["day_of_week"], str(r["day_of_week"])), "count": r["count"]}
                for r in top_days
            ],
            "top_years": [
                {"year": r["year"], "count": r["count"]}
                for r in top_years
            ],
        }

    except Exception as e:
        logger.error(f"Erreur get_best_periods : {e}", exc_info=True)
        return {"top_months": [], "top_days_of_week": [], "top_years": []}
    finally:
        if cursor:
            cursor.close()


# ---------------------------------------------------------------------------
# 3. Classement des ateliers les plus fréquentés
# ---------------------------------------------------------------------------

def get_top_ateliers(
    connection: pymysql.connections.Connection,
    limit: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retourne le classement des ateliers (atelier_name / atelier_id) par
    nombre de formules associées.

    Returns:
        Liste de {atelier_id, atelier_name, count} triée par count DESC
    """
    cursor = None
    try:
        cursor = connection.cursor()

        conditions = ["customer_id IS NOT NULL", "atelier_name IS NOT NULL", "TRIM(atelier_name) != ''"]
        params: List[Any] = []

        if date_from:
            conditions.append("DATE(created_at) >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("DATE(created_at) <= %s")
            params.append(date_to)

        where_clause = "WHERE " + " AND ".join(conditions)

        cursor.execute(f"""
            SELECT atelier_id, TRIM(atelier_name) AS atelier_name, COUNT(*) AS count
            FROM formula
            {where_clause}
            GROUP BY atelier_id, TRIM(atelier_name)
            ORDER BY count DESC
            LIMIT %s
        """, params + [limit])

        rows = cursor.fetchall() or []
        return [dict(r) for r in rows]

    except Exception as e:
        logger.error(f"Erreur get_top_ateliers : {e}", exc_info=True)
        return []
    finally:
        if cursor:
            cursor.close()


# ---------------------------------------------------------------------------
# 4. Classement des notes les plus utilisées
# ---------------------------------------------------------------------------

def get_top_notes(
    connection: pymysql.connections.Connection,
    limit: int = 20,
    note_type: Optional[str] = None,  # "top_note"|"heart_note"|"base_note"|"booster_note"|None=all
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retourne le classement des notes (essences) les plus utilisées, en ne prenant
    en compte que les formules associées à des clients validés (customer_id IS NOT NULL)
    et en excluant les placeholders 'A définir' / vides.

    Args:
        note_type: Filtrer par type de note. Si None, toutes les notes sont agrégées.
        limit:     Nombre max de résultats par type / global.

    Returns:
        Dict avec une clé par type de note (ou 'all') + un top global si toutes demandées.
    """
    cursor = None
    note_tables = ["top_note", "heart_note", "base_note", "booster_note"]
    if note_type and note_type in note_tables:
        note_tables = [note_type]

    try:
        cursor = connection.cursor()

        date_conditions = []
        date_params: List[Any] = []
        if date_from:
            date_conditions.append("DATE(f.created_at) >= %s")
            date_params.append(date_from)
        if date_to:
            date_conditions.append("DATE(f.created_at) <= %s")
            date_params.append(date_to)
        date_where = ("AND " + " AND ".join(date_conditions)) if date_conditions else ""

        # Condition pour exclure les valeurs vides et le placeholder 'A définir'
        note_filter = "n.name IS NOT NULL AND TRIM(n.name) != '' AND LOWER(TRIM(n.name)) NOT IN ('a définir', 'a definir')"

        result: Dict[str, Any] = {}

        for table in note_tables:
            query = f"""
                SELECT TRIM(n.name) AS name, COUNT(*) AS count
                FROM {table} n
                JOIN formula f ON f.id = n.formula_id
                WHERE f.customer_id IS NOT NULL
                  AND {note_filter}
                  {date_where}
                GROUP BY TRIM(n.name)
                ORDER BY count DESC
                LIMIT %s
            """
            cursor.execute(query, date_params + [limit])
            result[table] = [dict(r) for r in cursor.fetchall()]

        # Top global (toutes tables UNION ALL)
        # On force CONVERT ... USING utf8mb4 pour éviter l'erreur "Illegal mix of collations"
        if len(note_tables) > 1 or note_type is None:
            union_parts = [
                f"SELECT CONVERT(TRIM(n.name) USING utf8mb4) AS name FROM {t} n JOIN formula f ON f.id = n.formula_id WHERE f.customer_id IS NOT NULL AND {note_filter} {date_where}"
                for t in ["top_note", "heart_note", "base_note", "booster_note"]
            ]
            union_query = f"""
                SELECT name, COUNT(*) AS count
                FROM ({" UNION ALL ".join(union_parts)}) AS all_notes
                GROUP BY name
                ORDER BY count DESC
                LIMIT %s
            """
            all_params = date_params * 4 + [limit]
            cursor.execute(union_query, all_params)
            result["all"] = [dict(r) for r in cursor.fetchall()]

        return result

    except Exception as e:
        logger.error(f"Erreur get_top_notes : {e}", exc_info=True)
        return {}
    finally:
        if cursor:
            cursor.close()


# ---------------------------------------------------------------------------
# 5. Classement des options les plus choisies
# ---------------------------------------------------------------------------

def get_top_options(
    connection: pymysql.connections.Connection,
    limit: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retourne le classement des options (formula_option.name) les plus choisies
    pour les formules associées à des clients validés.

    Returns:
        Liste de {option_name, count} triée par count DESC
    """
    cursor = None
    try:
        cursor = connection.cursor()

        conditions = ["f.customer_id IS NOT NULL", "fo.name IS NOT NULL", "TRIM(fo.name) != ''"]
        params: List[Any] = []

        if date_from:
            conditions.append("DATE(f.created_at) >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("DATE(f.created_at) <= %s")
            params.append(date_to)

        where_clause = "WHERE " + " AND ".join(conditions)

        cursor.execute(f"""
            SELECT TRIM(fo.name) AS option_name, COUNT(*) AS count
            FROM formula_option fo
            JOIN formula f ON f.id = fo.formula_id
            {where_clause}
            GROUP BY TRIM(fo.name)
            ORDER BY count DESC
            LIMIT %s
        """, params + [limit])

        return [dict(r) for r in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Erreur get_top_options : {e}", exc_info=True)
        return []
    finally:
        if cursor:
            cursor.close()


# ---------------------------------------------------------------------------
# 6. Pourcentage client Homme / Femme
# ---------------------------------------------------------------------------

def get_gender_distribution(
    connection: pymysql.connections.Connection,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retourne la répartition Homme / Femme / Non renseigné des clients.

    Returns:
        Dict {male, female, unknown, total, male_pct, female_pct, unknown_pct}
    """
    cursor = None
    try:
        cursor = connection.cursor()

        conditions = []
        params: List[Any] = []

        if date_from:
            conditions.append("DATE(created_at) >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("DATE(created_at) <= %s")
            params.append(date_to)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        cursor.execute(f"""
            SELECT
                SUM(CASE WHEN LOWER(TRIM(gender)) = 'homme' THEN 1 ELSE 0 END) AS male,
                SUM(CASE WHEN LOWER(TRIM(gender)) = 'femme' THEN 1 ELSE 0 END) AS female,
                COUNT(*) AS total
            FROM customers
            {where_clause}
        """, params)

        row = cursor.fetchone() or {}
        male = int(row.get("male") or 0)
        female = int(row.get("female") or 0)
        total = int(row.get("total") or 0)
        unknown = max(0, total - (male + female))

        known = male + female
        male_pct = round(male / known * 100, 2) if known > 0 else 0.0
        female_pct = round(female / known * 100, 2) if known > 0 else 0.0
        unknown_pct = round(unknown / total * 100, 2) if total > 0 else 0.0

        return {
            "male": male,
            "female": female,
            "unknown": unknown,
            "total": total,
            "male_pct": male_pct,
            "female_pct": female_pct,
            "unknown_pct": unknown_pct,
        }

    except Exception as e:
        logger.error(f"Erreur get_gender_distribution : {e}", exc_info=True)
        return {"male": 0, "female": 0, "unknown": 0, "total": 0, "male_pct": 0.0, "female_pct": 0.0, "unknown_pct": 0.0}
    finally:
        if cursor:
            cursor.close()


# ---------------------------------------------------------------------------
# 7. Classement clients par ville / pays
# ---------------------------------------------------------------------------

def get_top_locations(
    connection: pymysql.connections.Connection,
    limit: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retourne les classements des villes et pays avec le plus de clients.

    Returns:
        Dict {top_countries, top_cities}
    """
    cursor = None
    try:
        cursor = connection.cursor()

        conditions = []
        params: List[Any] = []

        if date_from:
            conditions.append("DATE(created_at) >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("DATE(created_at) <= %s")
            params.append(date_to)

        base_where = ("AND " + " AND ".join(conditions)) if conditions else ""

        # Top pays
        cursor.execute(f"""
            SELECT TRIM(country) AS country, COUNT(*) AS count
            FROM customers
            WHERE country IS NOT NULL AND TRIM(country) != ''
            {base_where}
            GROUP BY TRIM(country)
            ORDER BY count DESC
            LIMIT %s
        """, params + [limit])
        top_countries = [dict(r) for r in cursor.fetchall()]

        # Top villes
        cursor.execute(f"""
            SELECT TRIM(city) AS city, COUNT(*) AS count
            FROM customers
            WHERE city IS NOT NULL AND TRIM(city) != ''
            {base_where}
            GROUP BY TRIM(city)
            ORDER BY count DESC
            LIMIT %s
        """, params + [limit])
        top_cities = [dict(r) for r in cursor.fetchall()]

        return {
            "top_countries": top_countries,
            "top_cities": top_cities,
        }

    except Exception as e:
        logger.error(f"Erreur get_top_locations : {e}", exc_info=True)
        return {"top_countries": [], "top_cities": []}
    finally:
        if cursor:
            cursor.close()


# ---------------------------------------------------------------------------
# 8. Taux de fidélité
# ---------------------------------------------------------------------------

def get_loyalty_rate(
    connection: pymysql.connections.Connection,
    min_formulas: int = 2,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calcule le taux de fidélité des clients :
    - Clients fidèles = ceux ayant >= min_formulas formules
    - Répartition par nombre de formules (1, 2, 3, 4, 5+)
    - Évolution mensuelle des nouveaux clients fidèles (clients atteignant leur Nième formule)

    Returns:
        Dict {total_customers_with_formula, loyal_customers, loyalty_rate, distribution, new_loyal_by_month}
    """
    cursor = None
    try:
        cursor = connection.cursor()

        date_conditions = []
        date_params: List[Any] = []
        if date_from:
            date_conditions.append("DATE(f.created_at) >= %s")
            date_params.append(date_from)
        if date_to:
            date_conditions.append("DATE(f.created_at) <= %s")
            date_params.append(date_to)
        date_where = ("AND " + " AND ".join(date_conditions)) if date_conditions else ""

        # Total clients distincts ayant au moins une formule sur la période
        cursor.execute(f"""
            SELECT COUNT(DISTINCT customer_id) AS total
            FROM formula f
            WHERE customer_id IS NOT NULL
            {date_where}
        """, date_params)
        total = (cursor.fetchone() or {}).get("total", 0)

        # Clients fidèles (>= min_formulas sur la période)
        cursor.execute(f"""
            SELECT COUNT(*) AS loyal
            FROM (
                SELECT customer_id
                FROM formula f
                WHERE customer_id IS NOT NULL
                {date_where}
                GROUP BY customer_id
                HAVING COUNT(*) >= %s
            ) AS sub
        """, date_params + [min_formulas])
        loyal = (cursor.fetchone() or {}).get("loyal", 0)

        loyalty_rate = round(loyal / total * 100, 2) if total > 0 else 0.0

        # Distribution par nombre de formules (1, 2, 3, 4, 5+)
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN formula_count >= 5 THEN '5+'
                    ELSE CAST(formula_count AS CHAR)
                END AS bucket,
                COUNT(*) AS customer_count
            FROM (
                SELECT customer_id, COUNT(*) AS formula_count
                FROM formula f
                WHERE customer_id IS NOT NULL
                {date_where}
                GROUP BY customer_id
            ) AS sub
            GROUP BY bucket
            ORDER BY MIN(formula_count) ASC
        """, date_params)
        distribution = [dict(r) for r in cursor.fetchall()]

        # Évolution mensuelle du nb de clients ayant passé leur Nième formule (N = min_formulas)
        # = clients dont la Nième formule (ordonnée chronologiquement) est validée
        nth_date_conditions = []
        nth_date_params: List[Any] = [min_formulas]
        if date_from:
            nth_date_conditions.append("DATE(nth.created_at) >= %s")
            nth_date_params.append(date_from)
        if date_to:
            nth_date_conditions.append("DATE(nth.created_at) <= %s")
            nth_date_params.append(date_to)
        nth_date_where = ("AND " + " AND ".join(nth_date_conditions)) if nth_date_conditions else ""

        cursor.execute(f"""
            SELECT DATE_FORMAT(nth.created_at, '%%Y-%%m') AS month, COUNT(*) AS new_loyal
            FROM (
                SELECT f.customer_id, f.created_at,
                       ROW_NUMBER() OVER (PARTITION BY f.customer_id ORDER BY f.created_at ASC, f.id ASC) AS rn
                FROM formula f
                WHERE f.customer_id IS NOT NULL
            ) AS nth
            WHERE nth.rn = %s
              AND nth.created_at IS NOT NULL
              {nth_date_where}
            GROUP BY month
            ORDER BY month ASC
        """, nth_date_params)
        by_month = [dict(r) for r in cursor.fetchall()]

        return {
            "total_customers_with_formula": total,
            "loyal_customers": loyal,
            "loyalty_rate": loyalty_rate,
            "min_formulas_threshold": min_formulas,
            "distribution": distribution,
            "new_loyal_by_month": by_month,
        }

    except Exception as e:
        logger.error(f"Erreur get_loyalty_rate : {e}", exc_info=True)
        return {
            "total_customers_with_formula": 0,
            "loyal_customers": 0,
            "loyalty_rate": 0.0,
            "min_formulas_threshold": min_formulas,
            "distribution": [],
            "new_loyal_by_month": [],
        }
    finally:
        if cursor:
            cursor.close()
