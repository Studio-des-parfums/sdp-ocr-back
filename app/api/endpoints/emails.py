import os
import base64
from fastapi import APIRouter, HTTPException
from app.schemas.email_schemas import EmailTestRequest, PyramidRequest, EmailResponse, PyramidPreviewResponse
from app.services.email.email_sender_service import email_sender_service
from app.database.connection import get_connection
from app.crud import crud_formula, crud_customer, crud_notes

router = APIRouter()

STATIC_PATH = os.path.join(os.path.dirname(__file__), "../../static/images")
PYRAMID_IMAGE_PATH = os.path.join(STATIC_PATH, "pyramide.png")


def get_pyramid_image_bytes():
    try:
        if os.path.exists(PYRAMID_IMAGE_PATH):
            with open(PYRAMID_IMAGE_PATH, "rb") as img_file:
                return img_file.read()
    except Exception as e:
        print(f"Erreur lecture image pyramide: {e}")
    return None


def _format_notes_html(notes):
    if not notes:
        return "<p style='margin:0'>—</p>"
    return "".join(
        f"<p style='margin:3px 0;font-size:14px'>{n['name']}</p>"
        for n in notes
    )


def _build_pyramid_html(customer, formula, top_notes, heart_notes, base_notes, percentages, preview=False):
    """Construit le HTML de la pyramide olfactive.
    Si preview=True, l'image est encodée en base64 data URI pour affichage navigateur.
    Si preview=False, l'image utilise cid: pour l'envoi email.
    """
    pyramid_image_bytes = get_pyramid_image_bytes()

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
<td style="font-size:15px;line-height:1.6">
<p>Bonjour {customer.get("last_name","")} {customer.get("first_name","")},</p>

<p>Nous avons le plaisir de vous transmettre la pyramide olfactive de votre création.</p>

<div style="margin:20px 0; display:flex; justify-content:center;">
    <span style="font-size:22px;font-weight:bold;color:#c00000;border:2px solid #c00000;padding:10px 18px;display:inline-block">
        {formula.get("perfume_name","")}
    </span>
</div>

<p>
Cette composition a été créée le {formula.get("date","")} et enregistrée sous la référence
<strong>{formula.get("reference","")}</strong>.
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

<h3 style="margin:0 0 8px;font-size:16px;border-bottom:1px solid #ddd">Notes de tête – {percentages['top']}%</h3>
{_format_notes_html(top_notes)}

<br>

<h3 style="margin:10px 0 8px;font-size:16px;border-bottom:1px solid #ddd">Notes de cœur – {percentages['heart']}%</h3>
{_format_notes_html(heart_notes)}

<br>

<h3 style="margin:10px 0 8px;font-size:16px;border-bottom:1px solid #ddd">Notes de fond – {percentages['base']}%</h3>
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


def _parse_quantity(note):
    try:
        return float(note.get("quantity") or 0)
    except (ValueError, TypeError):
        return 0


def _top_notes_by_quantity(notes, limit=3):
    """Trie les notes par quantité décroissante et retourne les `limit` premières."""
    return sorted(notes, key=_parse_quantity, reverse=True)[:limit]


def _sum_quantities(notes):
    """Retourne la somme des quantités d'une liste de notes."""
    return sum(_parse_quantity(n) for n in notes)


def _get_pyramid_data(connection, reference):
    """Récupère les données nécessaires pour construire la pyramide."""
    formula = crud_formula.get_by_reference(connection, reference)
    if not formula:
        raise HTTPException(status_code=404, detail="Formule non trouvee")

    customer = crud_customer.get_by_id(connection, formula["customer_id"])
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouve")

    all_top = crud_notes.get_notes_by_type(connection, "top_note", formula["id"])
    all_heart = crud_notes.get_notes_by_type(connection, "heart_note", formula["id"])
    all_base = crud_notes.get_notes_by_type(connection, "base_note", formula["id"])

    # Calcul des pourcentages sur TOUTES les notes
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

    # Top 3 par quantité pour l'affichage
    top_notes = _top_notes_by_quantity(all_top)
    heart_notes = _top_notes_by_quantity(all_heart)
    base_notes = _top_notes_by_quantity(all_base)

    return formula, customer, top_notes, heart_notes, base_notes, percentages


@router.post("/test", response_model=EmailResponse)
async def send_test_email(request: EmailTestRequest):
    try:
        result = email_sender_service.send_test_email(to_email=request.to_email)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pyramid/preview", response_model=PyramidPreviewResponse)
async def preview_pyramid_email(request: PyramidRequest):
    """Retourne le HTML de la pyramide pour prévisualisation sans envoyer l'email."""
    connection = None
    try:
        connection = get_connection()
        if not connection:
            raise HTTPException(status_code=500, detail="Erreur de connexion a la base de donnees")

        formula, customer, top_notes, heart_notes, base_notes, percentages = _get_pyramid_data(connection, request.reference)

        subject = "Votre pyramide olfactive – Le Studio des Parfums"
        html = _build_pyramid_html(customer, formula, top_notes, heart_notes, base_notes, percentages, preview=True)

        return PyramidPreviewResponse(
            subject=subject,
            html=html,
            to_email=customer.get("email"),
            customer_name=f"{customer.get('last_name', '')} {customer.get('first_name', '')}".strip()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            connection.close()


@router.post("/pyramid", response_model=EmailResponse)
async def send_pyramid_email(request: PyramidRequest):
    connection = None
    try:
        connection = get_connection()
        if not connection:
            raise HTTPException(status_code=500, detail="Erreur de connexion a la base de donnees")

        formula, customer, top_notes, heart_notes, base_notes, percentages = _get_pyramid_data(connection, request.reference)

        subject = "Votre pyramide olfactive – Le Studio des Parfums"
        body = _build_pyramid_html(customer, formula, top_notes, heart_notes, base_notes, percentages, preview=False)

        pyramid_image_bytes = get_pyramid_image_bytes()
        inline_images = []
        if pyramid_image_bytes:
            inline_images.append({
                "cid": "pyramid_image",
                "content": pyramid_image_bytes,
                "subtype": "png",
                "filename": "pyramide.png"
            })

        result = email_sender_service.send_email(
            to_email=customer.get("email"),
            subject=subject,
            body=body,
            is_html=True,
            inline_images=inline_images
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            connection.close()
