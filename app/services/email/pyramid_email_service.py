"""
Email de pyramide olfactive envoyé au client après validation de sa formule
(que ce soit via scan/OCR ou via le parcours tablette). Voir app/api/endpoints/emails.py
pour les routes manuelles (test/preview) et app/api/endpoints/tablet.py pour l'envoi
automatique déclenché à la soumission.
"""

import base64

from app.crud import crud_customer, crud_formula, crud_notes
from app.services.email.email_assets import get_logo_image_bytes, get_pyramid_image_bytes
from app.services.email.email_sender_service import email_sender_service


def _format_notes_html(notes):
    if not notes:
        return "<p style='margin:0'>—</p>"
    return "".join(f"<p style='margin:3px 0;font-size:14px'>{n['name']}</p>" for n in notes)


def _parse_quantity(note):
    try:
        return float(note.get("quantity") or 0)
    except (ValueError, TypeError):
        return 0


def _top_notes_by_quantity(notes, limit=3):
    """Trie les notes par quantité décroissante et retourne les `limit` premières."""
    return sorted(notes, key=_parse_quantity, reverse=True)[:limit]


def _sum_quantities(notes):
    return sum(_parse_quantity(n) for n in notes)


def build_pyramid_html(
    customer, formula, top_notes, heart_notes, base_notes, percentages, preview=False
):
    """Construit le HTML de la pyramide olfactive.
    Si preview=True, les images sont encodées en base64 data URI pour affichage navigateur.
    Si preview=False, les images utilisent cid: pour l'envoi email.
    """
    pyramid_image_bytes = get_pyramid_image_bytes()
    logo_image_bytes = get_logo_image_bytes()

    if pyramid_image_bytes:
        if preview:
            b64 = base64.b64encode(pyramid_image_bytes).decode("utf-8")
            pyramid_img_tag = f"""
                <img src="data:image/png;base64,{b64}"
                     alt="Pyramide olfactive"
                     style="width:100%; max-width:260px; height:auto; display:block;">
            """
        else:
            pyramid_img_tag = """
                <img src="cid:pyramid_image"
                     alt="Pyramide olfactive"
                     style="width:100%; max-width:260px; height:auto; display:block;">
            """
    else:
        pyramid_img_tag = "<div style='width:260px;height:200px;background:#eee'></div>"

    if logo_image_bytes:
        if preview:
            logo_b64 = base64.b64encode(logo_image_bytes).decode("utf-8")
            logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" alt="Le Studio des Parfums" style="height:60px;display:block;margin:0 auto 10px;">'
        else:
            logo_img_tag = '<img src="cid:logo_image" alt="Le Studio des Parfums" style="height:60px;display:block;margin:0 auto 10px;">'
    else:
        logo_img_tag = ""

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>

<body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;color:#333">

<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="left" style="padding:30px">

<!-- CONTENEUR PRINCIPAL -->
<table width="700" cellpadding="0" cellspacing="0" style="max-width:700px">

<tr>
<td align="center" style="padding-bottom:20px">
{logo_img_tag}
</td>
</tr>

<tr>
<td style="font-size:15px;line-height:1.6">
<p>Bonjour {customer.get("last_name", "")} {customer.get("first_name", "")},</p>

<p>Nous avons le plaisir de vous transmettre la pyramide olfactive de votre création.</p>

<div style="margin:20px 0; display:flex; justify-content:center;">
    <span style="font-size:22px;font-weight:bold;color:#c00000;border:2px solid #c00000;padding:10px 18px;display:inline-block">
        {formula.get("perfume_name", "")}
    </span>
</div>

<p>
Cette composition a été créée le {formula.get("date", "")} et enregistrée sous la référence
<strong>{formula.get("reference", "")}</strong>.
</p>
</td>
</tr>

<!-- ESPACE -->
<tr><td height="20"></td></tr>

<!-- LAYOUT DEUX COLONNES -->
<tr>
<td>
<table width="100%" cellpadding="0" cellspacing="0">
<tr>

<!-- COLONNE DROITE (50%) -->
<td width="50%" valign="top" align="center" height="700">
{pyramid_img_tag}
</td>

<!-- COLONNE GAUCHE (50%) -->
<td width="50%" valign="top" style="padding-right:25px">

<h3 style="margin:0 0 8px;font-size:16px;border-bottom:1px solid #ddd">Notes de tête – {percentages["top"]}%</h3>
{_format_notes_html(top_notes)}

<br>

<h3 style="margin:10px 0 8px;font-size:16px;border-bottom:1px solid #ddd">Notes de cœur – {percentages["heart"]}%</h3>
{_format_notes_html(heart_notes)}

<br>

<h3 style="margin:10px 0 8px;font-size:16px;border-bottom:1px solid #ddd">Notes de fond – {percentages["base"]}%</h3>
{_format_notes_html(base_notes)}

</td>

</tr>
</table>
</td>
</tr>

<!-- MESSAGE IMPORTANT -->
<tr>
<td style="padding-top:30px">
<p style="color:#c00000;font-weight:bold">
Nous vous rappelons que vous pouvez recommander dès que vous le souhaitez.
</p>
</td>
</tr>

<!-- FOOTER -->
<tr>
<td style="padding-top:30px;font-size:12px;color:#666;text-align:center">
<hr style="border:none;border-top:2px solid #333;margin-bottom:15px;text-align:center">
<strong>Le Studio des Parfums – Paris</strong><br>
23 rue du Bourg Tibourg – 75004 Paris<br>
Tél : +33 (0)1 40 29 90 84<br>
www.studiodesparfums-paris.fr
</td>
</tr>

</table>
</td>
</tr>
</table>

</body>
</html>
"""


def get_pyramid_data(connection, reference=None, formula_id=None):
    """Récupère les données nécessaires pour construire la pyramide, par reference ou formula_id.
    Retourne None si la formule ou le client n'existe pas."""
    if formula_id is not None:
        formula = crud_formula.get_by_id(connection, formula_id)
    elif reference:
        formula = crud_formula.get_by_reference(connection, reference)
    else:
        return None

    if not formula:
        return None

    customer = crud_customer.get_by_id(connection, formula["customer_id"])
    if not customer:
        return None

    all_top = crud_notes.get_notes_by_type(connection, "top_note", formula["id"])
    all_heart = crud_notes.get_notes_by_type(connection, "heart_note", formula["id"])
    all_base = crud_notes.get_notes_by_type(connection, "base_note", formula["id"])

    total_top = _sum_quantities(all_top)
    total_heart = _sum_quantities(all_heart)
    total_base = _sum_quantities(all_base)
    grand_total = total_top + total_heart + total_base

    if grand_total > 0:
        percentages = {
            "top": round(total_top / grand_total * 100),
            "heart": round(total_heart / grand_total * 100),
            "base": round(total_base / grand_total * 100),
        }
    else:
        percentages = {"top": 0, "heart": 0, "base": 0}

    top_notes = _top_notes_by_quantity(all_top)
    heart_notes = _top_notes_by_quantity(all_heart)
    base_notes = _top_notes_by_quantity(all_base)

    return formula, customer, top_notes, heart_notes, base_notes, percentages


def send_pyramid_email_for_formula(connection, formula_id: int) -> dict:
    """Construit et envoie l'email de pyramide olfactive pour une formule donnée.
    Returns dict {success, message}. Ne lève pas d'exception : toute erreur
    (formule/client introuvable, échec Resend, etc.) est renvoyée dans le dict."""
    data = get_pyramid_data(connection, formula_id=formula_id)
    if not data:
        return {"success": False, "message": "Formule ou client introuvable"}

    formula, customer, top_notes, heart_notes, base_notes, percentages = data

    to_email = customer.get("email")
    if not to_email:
        return {"success": False, "message": "Le client n'a pas d'adresse email"}

    subject = "Votre pyramide olfactive – Le Studio des Parfums"
    body = build_pyramid_html(
        customer, formula, top_notes, heart_notes, base_notes, percentages, preview=False
    )

    pyramid_image_bytes = get_pyramid_image_bytes()
    logo_image_bytes = get_logo_image_bytes()
    inline_images = []
    if pyramid_image_bytes:
        inline_images.append(
            {
                "cid": "pyramid_image",
                "content": pyramid_image_bytes,
                "subtype": "png",
                "filename": "pyramide.png",
            }
        )
    if logo_image_bytes:
        inline_images.append(
            {
                "cid": "logo_image",
                "content": logo_image_bytes,
                "subtype": "png",
                "filename": "logoSDP.png",
            }
        )

    return email_sender_service.send_email(
        to_email=to_email, subject=subject, body=body, is_html=True, inline_images=inline_images
    )
