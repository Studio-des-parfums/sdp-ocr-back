from datetime import date

from app.utils.date_parser import (
    extract_date_from_identifiant,
    parse_and_resolve_formula_date,
    resolve_ocr_date,
)


def test_extract_date_from_identifiant():
    # Format standard : YYYYMMDD + index
    assert extract_date_from_identifiant("202607145") == "2026-07-14"
    assert extract_date_from_identifiant("202201021") == "2022-01-02"
    assert extract_date_from_identifiant("2024123101") == "2024-12-31"

    # Avec espaces ou tirets parasites
    assert extract_date_from_identifiant(" 2026 07 14 5 ") == "2026-07-14"
    assert extract_date_from_identifiant("2026-07-14-5") == "2026-07-14"

    # Année bissextile
    assert extract_date_from_identifiant("202402291") == "2024-02-29"
    # Année non-bissextile (invalide -> None)
    assert extract_date_from_identifiant("202302291") is None

    # Identifiant sans date valide
    assert extract_date_from_identifiant("82201001") is None
    assert extract_date_from_identifiant(None) is None
    assert extract_date_from_identifiant("") is None


def test_resolve_ocr_date():
    # 1. Date explicite valide présente -> prioritaire
    assert resolve_ocr_date("14/07/2026", "202607145") == "2026-07-14"
    assert resolve_ocr_date("2026-07-14", "202607145") == "2026-07-14"
    assert resolve_ocr_date("02/01/22", None) == "2022-01-02"

    # 2. Date absente ou vide -> déduite de l'identifiant
    assert resolve_ocr_date(None, "202607145") == "2026-07-14"
    assert resolve_ocr_date("", "202607145") == "2026-07-14"
    assert resolve_ocr_date("   ", "202607145") == "2026-07-14"
    assert resolve_ocr_date("null", "202607145") == "2026-07-14"
    assert resolve_ocr_date(None, "202201021") == "2022-01-02"

    # 3. Ni date ni identifiant valide
    assert resolve_ocr_date(None, None) is None
    assert resolve_ocr_date(None, "82201001") is None


def test_parse_and_resolve_formula_date_with_identifiant_fallback():
    # Vérifie que la fonction système résout aussi le jour via l'identifiant
    res = parse_and_resolve_formula_date(None, raw_reference="202607145")
    assert res == date(2026, 7, 14)
