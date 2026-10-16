from collections import defaultdict
from datetime import datetime, date
from typing import Any, Dict, List, Optional
import pymysql

from app.core.logger import get_logger
from app.utils.date_parser import parse_and_resolve_formula_date

logger = get_logger(__name__)


def _parse_filter_date(d_str: Optional[str]) -> Optional[date]:
    """Parse une date de filtre au format YYYY-MM-DD."""
    if not d_str:
        return None
    try:
        return datetime.strptime(d_str.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _is_in_range(dt: Optional[date], d_from: Optional[date], d_to: Optional[date]) -> bool:
    """Vérifie si la date dt est dans la plage [d_from, d_to]."""
    if not dt:
        return False
    if d_from and dt < d_from:
        return False
    if d_to and dt > d_to:
        return False
    return True


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
    temporelle (par jour, mois ou année) calculée à partir de la date réelle de la formule
    (colonne formula.date, résolue et normalisée).
    """
    cursor = None
    try:
        cursor = connection.cursor()
        d_from = _parse_filter_date(date_from)
        d_to = _parse_filter_date(date_to)

        cursor.execute("""
            SELECT date, reference, created_at, COUNT(*) as c
            FROM formula
            WHERE customer_id IS NOT NULL
            GROUP BY date, reference, created_at
        """)
        rows = cursor.fetchall() or []

        counts_by_period: Dict[str, int] = defaultdict(int)
        total = 0

        for r in rows:
            dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
            if not _is_in_range(dt, d_from, d_to):
                continue

            count = r["c"]
            total += count

            if group_by == "day":
                key = dt.strftime("%Y-%m-%d")
            elif group_by == "year":
                key = dt.strftime("%Y")
            else:  # month (défaut)
                key = dt.strftime("%Y-%m")

            counts_by_period[key] += count

        sorted_data = [
            {"period": k, "count": counts_by_period[k]}
            for k in sorted(counts_by_period.keys())
        ]

        period_label = "date" if group_by == "day" else group_by

        return {
            "total": total,
            "group_by": group_by,
            "period_label": period_label,
            "data": sorted_data,
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
    Retourne les mois (1=Janvier…12=Décembre), jours de la semaine (1=Lundi…7=Dimanche)
    et années qui concentrent le plus de formules créées, selon la colonne formula.date.
    """
    cursor = None
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT date, reference, created_at, COUNT(*) as c
            FROM formula
            WHERE customer_id IS NOT NULL
            GROUP BY date, reference, created_at
        """)
        rows = cursor.fetchall() or []

        month_counts: Dict[int, int] = defaultdict(int)
        dow_counts: Dict[int, int] = defaultdict(int)  # 1=Lundi, 7=Dimanche
        year_counts: Dict[int, int] = defaultdict(int)

        for r in rows:
            dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
            if not dt:
                continue

            c = r["c"]
            month_counts[dt.month] += c
            # dt.isoweekday(): 1=Lundi, 7=Dimanche
            dow_counts[dt.isoweekday()] += c
            year_counts[dt.year] += c

        month_names = {
            1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
            5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
            9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
        }
        day_names = {
            1: "Lundi", 2: "Mardi", 3: "Mercredi", 4: "Jeudi",
            5: "Vendredi", 6: "Samedi", 7: "Dimanche"
        }

        top_months = sorted(month_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        top_days = sorted(dow_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        top_years = sorted(year_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return {
            "top_months": [
                {"month": m, "label": month_names.get(m, str(m)), "count": cnt}
                for m, cnt in top_months
            ],
            "top_days_of_week": [
                {"day": d, "label": day_names.get(d, str(d)), "count": cnt}
                for d, cnt in top_days
            ],
            "top_years": [
                {"year": y, "count": cnt}
                for y, cnt in top_years
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
    nombre de formules associées, filtré selon la date de la formule.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        d_from = _parse_filter_date(date_from)
        d_to = _parse_filter_date(date_to)

        cursor.execute("""
            SELECT atelier_id, TRIM(atelier_name) AS atelier_name, date, reference, created_at, COUNT(*) as c
            FROM formula
            WHERE customer_id IS NOT NULL AND atelier_name IS NOT NULL AND TRIM(atelier_name) != ''
            GROUP BY atelier_id, TRIM(atelier_name), date, reference, created_at
        """)
        rows = cursor.fetchall() or []

        atelier_counts: Dict[tuple, int] = defaultdict(int)

        for r in rows:
            dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
            if not _is_in_range(dt, d_from, d_to):
                continue
            key = (r["atelier_id"], r["atelier_name"])
            atelier_counts[key] += r["c"]

        sorted_ateliers = sorted(atelier_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {"atelier_id": aid, "atelier_name": aname, "count": cnt}
            for (aid, aname), cnt in sorted_ateliers
        ]

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
    Retourne le classement des notes (essences) les plus utilisées, en filtrant
    selon la date réelle des formules (formula.date) si des filtres temporels sont fournis.
    """
    cursor = None
    note_tables = ["top_note", "heart_note", "base_note", "booster_note"]
    if note_type and note_type in note_tables:
        note_tables = [note_type]

    try:
        cursor = connection.cursor()
        d_from = _parse_filter_date(date_from)
        d_to = _parse_filter_date(date_to)
        has_date_filter = bool(d_from or d_to)

        note_filter = "n.name IS NOT NULL AND TRIM(n.name) != '' AND LOWER(TRIM(n.name)) NOT IN ('a définir', 'a definir')"
        result: Dict[str, Any] = {}

        if not has_date_filter:
            # Sans filtre de dates : requête SQL directe hautement optimisée
            for table in note_tables:
                query = f"""
                    SELECT TRIM(n.name) AS name, COUNT(*) AS count
                    FROM {table} n
                    JOIN formula f ON f.id = n.formula_id
                    WHERE f.customer_id IS NOT NULL AND {note_filter}
                    GROUP BY TRIM(n.name)
                    ORDER BY count DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
                result[table] = [dict(r) for r in cursor.fetchall()]

            if len(note_tables) > 1 or note_type is None:
                union_parts = [
                    f"SELECT CONVERT(TRIM(n.name) USING utf8mb4) AS name FROM {t} n JOIN formula f ON f.id = n.formula_id WHERE f.customer_id IS NOT NULL AND {note_filter}"
                    for t in ["top_note", "heart_note", "base_note", "booster_note"]
                ]
                union_query = f"""
                    SELECT name, COUNT(*) AS count
                    FROM ({" UNION ALL ".join(union_parts)}) AS all_notes
                    GROUP BY name
                    ORDER BY count DESC
                    LIMIT %s
                """
                cursor.execute(union_query, (limit,))
                result["all"] = [dict(r) for r in cursor.fetchall()]

        else:
            # Avec filtre de dates : résolution des dates de formules
            all_counts: Dict[str, int] = defaultdict(int)

            for table in note_tables:
                query = f"""
                    SELECT f.date, f.reference, f.created_at, TRIM(n.name) as name, COUNT(*) as c
                    FROM {table} n
                    JOIN formula f ON f.id = n.formula_id
                    WHERE f.customer_id IS NOT NULL AND {note_filter}
                    GROUP BY f.date, f.reference, f.created_at, TRIM(n.name)
                """
                cursor.execute(query)
                table_counts: Dict[str, int] = defaultdict(int)

                for r in cursor.fetchall() or []:
                    dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
                    if not _is_in_range(dt, d_from, d_to):
                        continue
                    n_name = r["name"]
                    c = r["c"]
                    table_counts[n_name] += c
                    all_counts[n_name] += c

                sorted_table = sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
                result[table] = [{"name": k, "count": v} for k, v in sorted_table]

            if len(note_tables) > 1 or note_type is None:
                sorted_all = sorted(all_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
                result["all"] = [{"name": k, "count": v} for k, v in sorted_all]

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
    Retourne le classement des options (formula_option.name) les plus choisies,
    filtrées selon la date résolue de la formule.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        d_from = _parse_filter_date(date_from)
        d_to = _parse_filter_date(date_to)

        cursor.execute("""
            SELECT TRIM(fo.name) AS option_name, f.date, f.reference, f.created_at, COUNT(*) as c
            FROM formula_option fo
            JOIN formula f ON f.id = fo.formula_id
            WHERE f.customer_id IS NOT NULL AND fo.name IS NOT NULL AND TRIM(fo.name) != ''
            GROUP BY TRIM(fo.name), f.date, f.reference, f.created_at
        """)
        rows = cursor.fetchall() or []

        option_counts: Dict[str, int] = defaultdict(int)
        for r in rows:
            dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
            if not _is_in_range(dt, d_from, d_to):
                continue
            option_counts[r["option_name"]] += r["c"]

        sorted_options = sorted(option_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [{"option_name": k, "count": v} for k, v in sorted_options]

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
    Si date_from ou date_to est spécifié, filtre sur les clients ayant une formule
    datée dans cette plage.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        d_from = _parse_filter_date(date_from)
        d_to = _parse_filter_date(date_to)

        if not d_from and not d_to:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN LOWER(TRIM(gender)) = 'homme' THEN 1 ELSE 0 END) AS male,
                    SUM(CASE WHEN LOWER(TRIM(gender)) = 'femme' THEN 1 ELSE 0 END) AS female,
                    COUNT(*) AS total
                FROM customers
            """)
            row = cursor.fetchone() or {}
            male = int(row.get("male") or 0)
            female = int(row.get("female") or 0)
            total = int(row.get("total") or 0)
        else:
            cursor.execute("""
                SELECT c.id, c.gender, f.date, f.reference, f.created_at
                FROM customers c
                JOIN formula f ON f.customer_id = c.id
            """)
            cust_genders: Dict[int, str] = {}
            for r in cursor.fetchall() or []:
                dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
                if _is_in_range(dt, d_from, d_to):
                    cust_genders[r["id"]] = (r["gender"] or "").strip().lower()

            male = sum(1 for g in cust_genders.values() if g == "homme")
            female = sum(1 for g in cust_genders.values() if g == "femme")
            total = len(cust_genders)

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
    Retourne les classements des villes et pays avec le plus de clients,
    filtrés sur la plage de date de formule si spécifiée.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        d_from = _parse_filter_date(date_from)
        d_to = _parse_filter_date(date_to)

        if not d_from and not d_to:
            cursor.execute(f"""
                SELECT TRIM(country) AS country, COUNT(*) AS count
                FROM customers
                WHERE country IS NOT NULL AND TRIM(country) != ''
                GROUP BY TRIM(country)
                ORDER BY count DESC
                LIMIT %s
            """, (limit,))
            top_countries = [dict(r) for r in cursor.fetchall()]

            cursor.execute(f"""
                SELECT TRIM(city) AS city, COUNT(*) AS count
                FROM customers
                WHERE city IS NOT NULL AND TRIM(city) != ''
                GROUP BY TRIM(city)
                ORDER BY count DESC
                LIMIT %s
            """, (limit,))
            top_cities = [dict(r) for r in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT c.id, TRIM(c.country) as country, TRIM(c.city) as city, f.date, f.reference, f.created_at
                FROM customers c
                JOIN formula f ON f.customer_id = c.id
            """)
            matched_customers: Dict[int, tuple] = {}
            for r in cursor.fetchall() or []:
                dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
                if _is_in_range(dt, d_from, d_to):
                    matched_customers[r["id"]] = (r["country"] or "", r["city"] or "")

            country_counts: Dict[str, int] = defaultdict(int)
            city_counts: Dict[str, int] = defaultdict(int)

            for ctry, cty in matched_customers.values():
                if ctry:
                    country_counts[ctry] += 1
                if cty:
                    city_counts[cty] += 1

            top_countries = [
                {"country": k, "count": v}
                for k, v in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            ]
            top_cities = [
                {"city": k, "count": v}
                for k, v in sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            ]

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
    Calcule le taux de fidélité des clients basé sur la date réelle de création de formule :
    - Clients fidèles = ceux ayant >= min_formulas formules
    - Distribution par nombre de formules (1, 2, 3, 4, 5+)
    - Évolution mensuelle des nouveaux clients fidèles (mois de la Nième formule)
    """
    cursor = None
    try:
        cursor = connection.cursor()
        d_from = _parse_filter_date(date_from)
        d_to = _parse_filter_date(date_to)

        cursor.execute("""
            SELECT id, customer_id, date, reference, created_at
            FROM formula
            WHERE customer_id IS NOT NULL
        """)
        rows = cursor.fetchall() or []

        # Grouper les formules par client avec leur date résolue
        by_customer: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for r in rows:
            dt = parse_and_resolve_formula_date(r["date"], r["reference"], r["created_at"])
            # Si filtre de date actif, on ne conserve que les formules dans la plage
            if _is_in_range(dt, d_from, d_to):
                by_customer[r["customer_id"]].append({"id": r["id"], "date": dt})

        total = len(by_customer)
        loyal = sum(1 for flist in by_customer.values() if len(flist) >= min_formulas)
        loyalty_rate_val = round(loyal / total * 100, 2) if total > 0 else 0.0

        # Distribution par bucket
        bucket_counts: Dict[str, int] = defaultdict(int)
        for flist in by_customer.values():
            cnt = len(flist)
            b = "5+" if cnt >= 5 else str(cnt)
            bucket_counts[b] += 1

        distribution = [
            {"bucket": b, "customer_count": bucket_counts.get(b, 0)}
            for b in ["1", "2", "3", "4", "5+"]
            if bucket_counts.get(b, 0) > 0
        ]

        # Évolution mensuelle de l'atteinte du statut fidèle (date de la Nième formule)
        by_month_counts: Dict[str, int] = defaultdict(int)
        for flist in by_customer.values():
            if len(flist) >= min_formulas:
                sorted_f = sorted(flist, key=lambda x: (x["date"] or datetime.max.date(), x["id"]))
                nth_formula = sorted_f[min_formulas - 1]
                if nth_formula["date"]:
                    m = nth_formula["date"].strftime("%Y-%m")
                    by_month_counts[m] += 1

        new_loyal_by_month = [
            {"month": m, "new_loyal": by_month_counts[m]}
            for m in sorted(by_month_counts.keys())
        ]

        return {
            "total_customers_with_formula": total,
            "loyal_customers": loyal,
            "loyalty_rate": loyalty_rate_val,
            "min_formulas_threshold": min_formulas,
            "distribution": distribution,
            "new_loyal_by_month": new_loyal_by_month,
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
