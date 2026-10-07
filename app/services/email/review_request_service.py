"""
Email de demande d'avis Google, envoyé 24h après la création d'une formule
(parcours tablette). Voir app/services/review_scheduler.py pour le job qui
déclenche cet envoi périodiquement.
"""
from app.services.email.email_sender_service import email_sender_service
from app.services.email.email_assets import get_logo_image_bytes

# Lien Maps direct vers la fiche "Le Studio des Parfums" (panneau avis déjà ouvert) :
# le client clique sur "Rédiger un avis" depuis cette fiche. Un lien court dédié
# (search.google.com/local/writereview?placeid=...) nécessiterait le vrai Place ID
# récupéré depuis Google Business Profile, non disponible pour le moment.
GOOGLE_REVIEW_URL = (
    "https://www.google.com/maps/place/Le+Studio+des+Parfums/@48.8571327,2.3561527,17z/"
    "data=!4m8!3m7!1s0x47e66e02ca2c1727:0x2aeae9be2f815477!8m2!3d48.8571292!4d2.3587276!9m1!1b1!16s%2Fg%2F1tdg2jg5"
)


def _build_review_request_html(first_name: str, perfume_name: str, logo_cid: str | None) -> str:
    logo_img_tag = (
        f'<img src="cid:{logo_cid}" alt="Le Studio des Parfums" style="height:60px;display:block;margin:0 auto 20px;">'
        if logo_cid else ""
    )
    greeting = f"Bonjour {first_name}," if first_name else "Bonjour,"
    perfume_line = (
        f"<p>Nous espérons que votre parfum <strong>{perfume_name}</strong> vous plaît !</p>"
        if perfume_name else "<p>Nous espérons que votre création vous plaît !</p>"
    )

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f7f5f2;font-family:Arial,sans-serif;color:#333">
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="center" style="padding:40px 20px">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:8px;overflow:hidden">

<tr>
<td align="center" style="padding:35px 30px 10px">
{logo_img_tag}
</td>
</tr>

<tr>
<td style="padding:0 40px 10px;font-size:15px;line-height:1.6;text-align:center">
<p>{greeting}</p>
{perfume_line}
<p>Votre avis compte énormément pour nous et nous aide à faire connaître notre atelier.<br>
Auriez-vous une minute pour partager votre expérience ?</p>
</td>
</tr>

<tr>
<td align="center" style="padding:15px 30px 35px">
<a href="{GOOGLE_REVIEW_URL}"
   style="display:inline-block;background:#c00000;color:#ffffff;text-decoration:none;
          font-weight:bold;font-size:15px;padding:14px 32px;border-radius:30px;letter-spacing:0.5px">
  ★ Laisser un avis Google
</a>
</td>
</tr>

<tr>
<td style="padding:20px 30px 30px;font-size:12px;color:#666;text-align:center">
<hr style="border:none;border-top:1px solid #eee;margin-bottom:15px">
<strong>Le Studio des Parfums – Paris</strong><br>
23 rue du Bourg Tibourg – 75004 Paris<br>
Tél : +33 (0)1 40 29 90 84 — www.studiodesparfums-paris.fr
</td>
</tr>

</table>
</td>
</tr>
</table>
</body>
</html>
"""


def send_review_request_email(to_email: str, first_name: str, perfume_name: str | None) -> dict:
    """Envoie l'email de demande d'avis Google. Returns dict {success, message}."""
    logo_bytes = get_logo_image_bytes()
    inline_images = []
    logo_cid = None
    if logo_bytes:
        logo_cid = "review_logo_image"
        inline_images.append({
            "cid": logo_cid,
            "content": logo_bytes,
            "filename": "logoSDP.png",
        })

    html = _build_review_request_html(first_name, perfume_name, logo_cid)

    return email_sender_service.send_email(
        to_email=to_email,
        subject="Votre avis compte pour nous – Le Studio des Parfums",
        body=html,
        is_html=True,
        inline_images=inline_images,
    )
