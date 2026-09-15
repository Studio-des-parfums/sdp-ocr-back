"""
Génération de la "fiche formule" en PDF.

Reproduit la mise en page de la fiche papier physique remplie en institut
(en-tête "Le Studio des Parfums", bloc infos client, ligne "Votre Parfum"
avec la taille du flacon, puis les 3 tableaux quadrillés Notes de
tête/cœur/fond avec les paliers 30/50/100 ml), afin qu'une fiche générée
pour une formule créée digitalement soit visuellement cohérente avec les
fiches scannées.

Utilisé notamment pour les formules qui n'ont aucune fiche/document
associé (ex: formules créées digitalement) afin de fournir un
téléchargement de remplacement reprenant la même charte graphique.
"""
from io import BytesIO
from typing import Optional

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration


def _checkbox(checked: bool) -> str:
    return "☒" if checked else "☐"


def _format_notes_rows(notes: list, min_rows: int = 7) -> str:
    """Une ligne par note (nom + quantité en ml), complétée par des lignes vides
    pour conserver la hauteur du tableau papier."""
    rows = ""
    for n in notes:
        qty = n.get("quantity") or ""
        rows += (
            "<tr>"
            f"<td class='note-name'>{n.get('name', '')}</td>"
            f"<td class='note-qty'>{qty}</td>"
            "</tr>"
        )
    for _ in range(max(0, min_rows - len(notes))):
        rows += "<tr><td class='note-name'>&nbsp;</td><td class='note-qty'></td></tr>"
    return rows


def _size_rows(selected_size: Optional[str]) -> str:
    sizes = [("30", "6 - 8"), ("50", "12 - 16"), ("100", "20 - 30")]
    rows = ""
    for ml, usage in sizes:
        is_selected = selected_size == ml
        rows += (
            "<tr>"
            f"<td class='size-ml'>{ml} ml</td>"
            f"<td class='size-usage'>{usage}</td>"
            f"<td class='size-check'>{_checkbox(is_selected)}</td>"
            "</tr>"
        )
    return rows


def generate_formula_sheet_html(customer: dict, formula: dict) -> str:
    top_notes = formula.get("top_notes") or []
    heart_notes = formula.get("heart_notes") or []
    base_notes = formula.get("base_notes") or []

    last_name = customer.get("last_name") or customer.get("nom") or ""
    first_name = customer.get("first_name") or customer.get("prenom") or ""
    email = customer.get("email") or ""
    phone = customer.get("phone") or ""
    job = customer.get("job") or ""
    city = customer.get("city") or ""
    country = customer.get("country") or ""

    perfume_name = formula.get("perfume_name") or ""
    reference = formula.get("reference") or f"Formule #{formula.get('id', '')}"
    date = formula.get("date") or ""
    quantity = str(formula.get("quantity") or "").strip()
    selected_size = quantity if quantity in ("30", "50", "100") else None

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: A4;
        margin: 1.4cm;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        padding: 0;
        background: #ffffff;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #1a1a1a;
        font-size: 12px;
    }}
    table {{ border-collapse: collapse; width: 100%; }}

    .header {{
        text-align: center;
        padding-bottom: 10px;
        margin-bottom: 10px;
        border-bottom: 2px solid #1a1a1a;
    }}
    .header .brand {{
        font-size: 26px;
        letter-spacing: 2px;
        font-weight: bold;
        margin: 0;
    }}
    .header .brand-sub {{
        font-size: 12px;
        letter-spacing: 4px;
        color: #555;
        margin: 2px 0 0;
    }}
    .header .reference {{
        position: absolute;
        top: 0;
        right: 0;
        font-size: 11px;
        color: #555;
    }}
    .header-wrap {{ position: relative; }}

    .info-table td {{
        border: 1px solid #999;
        padding: 5px 8px;
        vertical-align: top;
        font-size: 11.5px;
    }}
    .info-table .label {{
        color: #555;
        margin-right: 4px;
    }}
    .civility span {{ margin-right: 14px; }}

    .parfum-bar {{
        margin: 14px 0 10px;
        text-align: center;
        border: 2px solid #1a1a1a;
        padding: 8px;
    }}
    .parfum-bar .title {{
        font-size: 13px;
        letter-spacing: 3px;
        font-weight: bold;
        margin-right: 16px;
    }}
    .parfum-bar .name {{
        font-size: 15px;
        font-weight: bold;
    }}

    .notes-section {{
        display: table;
        width: 100%;
        margin-bottom: 10px;
    }}
    .notes-block {{
        border: 1px solid #1a1a1a;
    }}
    .notes-block + .notes-block {{ margin-top: 10px; }}
    .notes-block .block-title {{
        background: #eee;
        font-weight: bold;
        font-size: 12px;
        padding: 5px 8px;
        border-bottom: 1px solid #1a1a1a;
    }}
    .notes-block table td, .notes-block table th {{
        border-bottom: 1px dotted #bbb;
        padding: 4px 8px;
        font-size: 11.5px;
    }}
    .notes-block table th {{
        text-align: left;
        color: #555;
        font-weight: normal;
        font-size: 10.5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid #1a1a1a;
    }}
    .note-name {{ width: 75%; }}
    .note-qty {{ width: 25%; color: #555; }}

    .size-box {{
        border: 1px solid #1a1a1a;
        margin-top: 4px;
    }}
    .size-box .block-title {{
        background: #eee;
        font-weight: bold;
        font-size: 11px;
        padding: 5px 8px;
        border-bottom: 1px solid #1a1a1a;
    }}
    .size-box table td {{
        border-bottom: 1px dotted #bbb;
        padding: 4px 8px;
        font-size: 11px;
    }}
    .size-check {{ text-align: center; width: 20%; }}

    .footer {{
        margin-top: 18px;
        padding-top: 10px;
        border-top: 2px solid #1a1a1a;
        text-align: center;
        font-size: 10.5px;
        color: #555;
    }}
</style>
</head>
<body>

<div class="header-wrap">
    <div class="reference">
        Réf. <strong>{reference}</strong>{f" — {date}" if date else ""}
    </div>
    <div class="header">
        <p class="brand">LE STUDIO DES PARFUMS</p>
        <p class="brand-sub">PARIS</p>
    </div>
</div>

<table class="info-table">
<tr>
    <td width="55%">
        <span class="label">Nom :</span><strong>{last_name}</strong><br>
        <span class="label">Prénom :</span><strong>{first_name}</strong><br>
        <span class="label">Profession :</span>{job}
    </td>
    <td width="45%">
        <span class="label">Tél :</span>{phone}<br>
        <span class="label">Email :</span>{email}<br>
        <span class="label">Ville :</span>{city} &nbsp; <span class="label">Pays :</span>{country}
    </td>
</tr>
</table>

<div class="parfum-bar">
    <span class="title">VOTRE PARFUM</span>
    <span class="name">{perfume_name}</span>
</div>

<div class="notes-section">
    <div class="notes-block">
        <div class="block-title">Notes de tête</div>
        <table>
            <tr><th class="note-name">Note</th><th class="note-qty">Qté en ml</th></tr>
            {_format_notes_rows(top_notes)}
        </table>
    </div>

    <div class="notes-block">
        <div class="block-title">Notes de cœur</div>
        <table>
            <tr><th class="note-name">Note</th><th class="note-qty">Qté en ml</th></tr>
            {_format_notes_rows(heart_notes)}
        </table>
    </div>

    <div class="notes-block">
        <div class="block-title">Notes de fond</div>
        <table>
            <tr><th class="note-name">Note</th><th class="note-qty">Qté en ml</th></tr>
            {_format_notes_rows(base_notes)}
        </table>
    </div>

    <div class="size-box">
        <div class="block-title">Taille du flacon</div>
        <table>
            <tr><td class="size-ml"><strong>Contenance</strong></td><td class="size-usage"><strong>Qté utile</strong></td><td class="size-check"></td></tr>
            {_size_rows(selected_size)}
        </table>
    </div>
</div>

<div class="footer">
    <strong>Le Studio des Parfums – Paris</strong><br>
    23 rue du Bourg Tibourg – 75004 Paris — Tél : +33 (0)1 40 29 90 84 — www.studiodesparfums-paris.fr
</div>

</body>
</html>
"""


def generate_formula_sheet_pdf(customer: dict, formula: dict) -> bytes:
    """Génère le PDF de la fiche formule (bytes prêts à être renvoyés en réponse HTTP)."""
    html_content = generate_formula_sheet_html(customer, formula)
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    pdf_buffer = BytesIO()
    html.write_pdf(pdf_buffer, font_config=font_config)
    return pdf_buffer.getvalue()
