import re
from datetime import date, datetime

import dateparser


def parse_and_resolve_formula_date(
    raw_date: str | date | datetime | None,
    raw_reference: str | None = None,
    created_at: datetime | date | None = None,
) -> date | None:
    """
    Formate et résout une date de formule à partir de la colonne `formula.date`.
    Comme les données proviennent de l'OCR manuscrit ou de saisies manuelles non formatées,
    cette fonction applique une batterie de filtres, expressions régulières et
    `dateparser` avec gestion multilingue (français/anglais), et s'appuie sur
    `reference` ou `created_at` en fallback.

    Args:
        raw_date: Valeur brute de la colonne `formula.date`
        raw_reference: Valeur de la colonne `formula.reference` (ex: '202512005')
        created_at: Valeur de la colonne `formula.created_at`

    Returns:
        date standardisée (datetime.date) ou None si irrésoluble.
    """
    if isinstance(raw_date, datetime):
        return raw_date.date()
    if isinstance(raw_date, date):
        return raw_date

    dt: date | None = None

    if raw_date:
        s = str(raw_date).strip()
        # Supprime la ponctuation de début/fin parasite
        s = re.sub(r"^[^\w\d]+|[^\w\d]+$", "", s)
        # Supprime les préfixes courants 'Le', 'du'
        s = re.sub(r"^(le|du)\s+", "", s, flags=re.IGNORECASE).strip()

        # 1. Format ISO : YYYY-MM-DD ou YYYY.MM.DD ou YYYY/MM/DD
        m_iso = re.match(r"^(20\d{2})[\/\.\-\s](\d{1,2})[\/\.\-\s](\d{1,2})$", s)
        if m_iso:
            try:
                dt = datetime(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))).date()
            except ValueError:
                pass

        # 2. Format standard français : DD/MM/YYYY ou DD/MM/YY
        if not dt:
            m = re.match(r"^(\d{1,2})[\/\.\-\s](\d{1,2})[\/\.\-\s](\d{2,4})$", s)
            if m:
                d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if y < 100:
                    y += 2000
                # Inversion américaine si mth > 12 (ex: 12/31/2024)
                if mth > 12 and d <= 12:
                    d, mth = mth, d
                try:
                    dt = datetime(y, mth, d).date()
                except ValueError:
                    pass

        # 3. Format collé 8 chiffres : DDMMYYYY (ex: 04052026)
        if not dt:
            m2 = re.match(r"^(\d{2})(\d{2})(20\d{2})$", s)
            if m2:
                try:
                    dt = datetime(int(m2.group(3)), int(m2.group(2)), int(m2.group(1))).date()
                except ValueError:
                    pass

        # 4. Format mois/année : MM/YYYY (défaut au 1er du mois)
        if not dt:
            m3 = re.match(r"^(\d{1,2})[\/\.\-](20\d{2})$", s)
            if m3:
                mth, y = int(m3.group(1)), int(m3.group(2))
                if 1 <= mth <= 12:
                    dt = datetime(y, mth, 1).date()

        # 5. Année seule : YYYY (défaut au 1er janvier)
        if not dt:
            m4 = re.match(r"^(20\d{2})$", s)
            if m4:
                dt = datetime(int(m4.group(1)), 1, 1).date()

        # 6. dateparser robuste pour le texte (ex: '27 juin 2025', '14 octobre 2025')
        if not dt:
            parsed = dateparser.parse(
                s,
                languages=["fr", "en"],
                settings={"DATE_ORDER": "DMY", "PREFER_DAY_OF_MONTH": "first"},
            )
            if parsed:
                dt = parsed.date()

    # Correction de cohérence : si l'année est manifestement hors intervalle (ex: typo OCR 2095 ou 1125),
    # on recale l'année sur la référence ou created_at
    if dt and (dt.year < 2000 or dt.year > 2030):
        corr_y = None
        if raw_reference:
            m_ref = re.match(r"^(20\d{2})", str(raw_reference).strip())
            if m_ref and 2000 <= int(m_ref.group(1)) <= 2030:
                corr_y = int(m_ref.group(1))
        if not corr_y and created_at:
            c_y = created_at.year if isinstance(created_at, (datetime, date)) else None
            if c_y and 2000 <= c_y <= 2030:
                corr_y = c_y
        if corr_y:
            try:
                dt = dt.replace(year=corr_y)
            except ValueError:
                dt = date(corr_y, dt.month, 1)

    # 7. Fallback référence : si la formule n'avait pas de date ou date illisible,
    # la référence/identifiant commence par la date YYYYMMDD (ex: 202607145 -> 2026-07-14)
    # ou YYYYMM (ex: 202512005 -> 2025-12-01)
    if not dt and raw_reference:
        ref = re.sub(r"[\s\-_]", "", str(raw_reference).strip())
        m_ref8 = re.match(r"^(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])", ref)
        if m_ref8:
            try:
                dt = date(int(m_ref8.group(1)), int(m_ref8.group(2)), int(m_ref8.group(3)))
            except ValueError:
                pass
        if not dt:
            m_ref6 = re.match(r"^(20\d{2})(0[1-9]|1[0-2])", ref)
            if m_ref6:
                y, mth = int(m_ref6.group(1)), int(m_ref6.group(2))
                if 1 <= mth <= 12:
                    dt = date(y, mth, 1)

    # 8. Dernier recours : created_at
    if not dt and created_at:
        dt = created_at.date() if isinstance(created_at, datetime) else created_at

    return dt


def extract_date_from_identifiant(identifiant: str | None) -> str | None:
    """
    Extrait une date au format 'YYYY-MM-DD' à partir d'un identifiant / numéro de création.
    Exemples :
        - '202607145' -> '2026-07-14' (2026-07-14 + index 5)
        - '202201021' -> '2022-01-02' (2022-01-02 + index 1)
        - '2024123101' -> '2024-12-31'
    """
    if not identifiant:
        return None
    clean = re.sub(r"[\s\-_]", "", str(identifiant))
    # 1. Si au moins 8 chiffres : doit commencer par un YYYYMMDD calendairement valide
    if len(clean) >= 8:
        m8 = re.match(r"^(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])", clean)
        if m8:
            y, m, d = int(m8.group(1)), int(m8.group(2)), int(m8.group(3))
            try:
                return date(y, m, d).strftime("%Y-%m-%d")
            except ValueError:
                return None
        return None

    # 2. Si 6 ou 7 chiffres (ex: 202607...)
    m6 = re.match(r"^(20\d{2})(0[1-9]|1[0-2])", clean)
    if m6:
        y, m = int(m6.group(1)), int(m6.group(2))
        try:
            return date(y, m, 1).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def resolve_ocr_date(raw_date: str | None, identifiant: str | None) -> str | None:
    """
    Résout et normalise la date d'une fiche OCR :
    1. Si `raw_date` est renseignée et non nulle, tente de la parser et normaliser au format 'YYYY-MM-DD'.
    2. Si `raw_date` est absente, vide, 'null' ou non résolue, déduit la date depuis `identifiant`.
    """
    if raw_date and str(raw_date).strip() and str(raw_date).strip().lower() != "null":
        parsed = parse_and_resolve_formula_date(raw_date, raw_reference=identifiant)
        if parsed:
            return parsed.strftime("%Y-%m-%d")

    # Fallback sur l'identifiant
    return extract_date_from_identifiant(identifiant)
