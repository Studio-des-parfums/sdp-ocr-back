import os
import base64
from io import BytesIO
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Chemin vers l'image de la pyramide
STATIC_PATH = os.path.join(os.path.dirname(__file__), "../../static/images")
PYRAMID_IMAGE_PATH = os.path.join(STATIC_PATH, "pyramide.png")


def get_pyramid_image_base64():
    """Retourne l'image de la pyramide encodee en base64"""
    try:
        if os.path.exists(PYRAMID_IMAGE_PATH):
            with open(PYRAMID_IMAGE_PATH, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Erreur lecture image pyramide: {e}")
    return None


def generate_pyramid_html(
    first_name: str,
    last_name: str,
    perfume_name: str,
    formula_date: str,
    reference: str,
    top_notes: list,
    heart_notes: list,
    base_notes: list,
    pyramid_image_base64: str = None
) -> str:
    """
    Genere le HTML pour la pyramide olfactive.
    Utilise pour le PDF et l'email.
    """

    def format_notes_html(notes):
        if not notes:
            return "<p>Aucune</p>"
        html = ""
        for note in notes:
            quantity = f" ({note['quantity']})" if note.get('quantity') else ""
            html += f"<p style='margin: 2px 0;'>{note['name']}{quantity}</p>"
        return html

    top_notes_html = format_notes_html(top_notes)
    heart_notes_html = format_notes_html(heart_notes)
    base_notes_html = format_notes_html(base_notes)

    # Image de la pyramide
    if pyramid_image_base64:
        pyramid_img_tag = f'<img src="data:image/png;base64,{pyramid_image_base64}" alt="Pyramide olfactive" style="max-width: 200px; height: auto;">'
    else:
        pyramid_img_tag = '<div style="width: 200px; height: 150px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #999;">[Pyramide]</div>'

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: Arial, sans-serif;
            color: #333;
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 100%;
        }}
        .perfume-name-wrapper {{
            text-align: center;
            margin: 20px 0;
        }}
        .perfume-name {{
            border: 2px solid #333;
            padding: 15px 30px;
            font-size: 24px;
            font-weight: bold;
            display: inline-block;
        }}
        .content-section {{
            display: table;
            width: 100%;
            margin: 30px 0;
        }}
        .pyramid-col {{
            display: table-cell;
            width: 40%;
            vertical-align: top;
            text-align: center;
            padding-right: 20px;
        }}
        .notes-col {{
            display: table-cell;
            width: 60%;
            vertical-align: top;
        }}
        .note-category {{
            margin-bottom: 15px;
        }}
        .note-title {{
            font-weight: bold;
            color: #555;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            margin-bottom: 5px;
        }}
        .reminder {{
            color: red;
            text-align: center;
            font-weight: bold;
            margin: 30px 0;
        }}
        .separator {{
            border-top: 2px solid #333;
            margin: 30px 0;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        .footer-title {{
            font-weight: bold;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <p>Bonjour {last_name} {first_name},</p>

        <p>Nous vous presentons la pyramide olfactive de votre creation :</p>

        <div class="perfume-name-wrapper">
            <div class="perfume-name">{perfume_name}</div>
        </div>

        <p>Ce parfum a ete cree le {formula_date} de type : </p>

        <p>Les familles olfactives sont : </p>

        <p>____, votre conseiller-parfumeur, a enregistre votre formule</p>

        <p>sous le numero <strong>{reference}</strong>, il s'agit d'une eau de parfum.</p>

        <div class="content-section">
            <div class="pyramid-col">
                {pyramid_img_tag}
            </div>
            <div class="notes-col">
                <div class="note-category">
                    <div class="note-title">Note de tete</div>
                    {top_notes_html}
                </div>
                <div class="note-category">
                    <div class="note-title">Note de coeur</div>
                    {heart_notes_html}
                </div>
                <div class="note-category">
                    <div class="note-title">Note de fond</div>
                    {base_notes_html}
                </div>
            </div>
        </div>

        <p class="reminder">Nous vous rappelons que vous pouvez recommander des que vous le souhaitez</p>

        <div class="separator"></div>

        <div class="footer">
            <p class="footer-title">Le Studio des Parfums - Paris</p>
            <p>23, rue du Bourg Tibourg - 75004 Paris / Tel : +33(0)1.40.29.90.84</p>
            <p>www.studiodesparfums-paris.fr / info@studiodesparfums-paris.fr</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_pyramid_pdf(
    first_name: str,
    last_name: str,
    perfume_name: str,
    formula_date: str,
    reference: str,
    top_notes: list,
    heart_notes: list,
    base_notes: list
) -> bytes:
    """
    Genere un PDF de la pyramide olfactive.

    Returns:
        bytes: Le contenu du PDF
    """
    # Recuperer l'image en base64
    pyramid_image_base64 = get_pyramid_image_base64()

    # Generer le HTML
    html_content = generate_pyramid_html(
        first_name=first_name,
        last_name=last_name,
        perfume_name=perfume_name,
        formula_date=formula_date,
        reference=reference,
        top_notes=top_notes,
        heart_notes=heart_notes,
        base_notes=base_notes,
        pyramid_image_base64=pyramid_image_base64
    )

    # Convertir en PDF
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    pdf_buffer = BytesIO()
    html.write_pdf(pdf_buffer, font_config=font_config)

    return pdf_buffer.getvalue()


# Instance du service
pyramid_pdf_service = {
    "generate_html": generate_pyramid_html,
    "generate_pdf": generate_pyramid_pdf,
    "get_pyramid_image_base64": get_pyramid_image_base64
}
