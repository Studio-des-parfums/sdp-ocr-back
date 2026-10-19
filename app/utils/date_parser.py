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
    # la référence suit la nomenclature YYYYMM... (ex: 202512005 -> 2025-12-01)
    if not dt and raw_reference:
        ref = str(raw_reference).strip()
        m_ref = re.match(r"^(20\d{2})(\d{2})", ref)
        if m_ref:
            y, mth = int(m_ref.group(1)), int(m_ref.group(2))
            if 1 <= mth <= 12:
                dt = date(y, mth, 1)

    # 8. Dernier recours : created_at
    if not dt and created_at:
        dt = created_at.date() if isinstance(created_at, datetime) else created_at

    return dt
