import asyncio
import base64
import io
import json
from typing import Any

from openai import AsyncOpenAI
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.ocr_schemas import DocumentAnnotation, DocumentType

logger = get_logger(__name__)


def _generate_markdown_from_annotation(ann: dict[str, Any]) -> str:
    """Génère une transcription markdown propre à partir des données annotées."""
    lines: list[str] = []
    doc_type = ann.get("document_type") or "unknown"

    if doc_type == DocumentType.STUDIO_PARFUMS.value or doc_type == "studio_parfums":
        lines.append("# LE STUDIO DES PARFUMS - FICHE DE CRÉATION")
        if ann.get("identifiant"):
            lines.append(f"Identifiant: {ann['identifiant']}")
        if ann.get("nom_parfum"):
            lines.append(f"Nom du parfum: {ann['nom_parfum']}")
        if ann.get("genre"):
            lines.append(f"Genre: {ann['genre']}")
        if ann.get("nom") or ann.get("prenom"):
            nom_complet = f"{ann.get('nom', '') or ''} {ann.get('prenom', '') or ''}".strip()
            lines.append(f"Nom / Prénom: {nom_complet}")
        if ann.get("email"):
            lines.append(f"Email: {ann['email']}")
        if ann.get("tel"):
            lines.append(f"Téléphone: {ann['tel']}")
        if ann.get("date"):
            lines.append(f"Date: {ann['date']}")
        if ann.get("ville"):
            lines.append(f"Ville: {ann['ville']}")
        if ann.get("pays"):
            lines.append(f"Pays: {ann['pays']}")
        if ann.get("profession"):
            lines.append(f"Profession: {ann['profession']}")
        if ann.get("date_naissance"):
            lines.append(f"Date de naissance: {ann['date_naissance']}")
        if ann.get("groupe"):
            lines.append(f"Groupe: {ann['groupe']}")

        for section_key, section_title in [
            ("notes_de_tete", "Notes de tête"),
            ("notes_de_coeur", "Notes de cœur"),
            ("notes_de_fond", "Notes de fond"),
        ]:
            notes = ann.get(section_key) or []
            if notes:
                lines.append(f"\n### {section_title}")
                for note in notes:
                    if isinstance(note, dict) and note.get("essence"):
                        qty = f" ({note['quantite_ml']} ml)" if note.get("quantite_ml") else ""
                        lines.append(f"- {note['essence']}{qty}")

    elif doc_type == DocumentType.BLANK_SHEET.value or doc_type == "blank_sheet":
        lines.append("# FEUILLE STATISTIQUE")
        if ann.get("month_year"):
            lines.append(f"Mois/Année: {ann['month_year']}")
        if ann.get("fiches_manquantes"):
            lines.append(f"Fiches manquantes: {', '.join(str(x) for x in ann['fiches_manquantes'])}")
        if ann.get("doublons"):
            lines.append(f"Doublons: {', '.join(str(x) for x in ann['doublons'])}")
        if ann.get("tel_list"):
            lines.append(f"Téléphones: {', '.join(str(x) for x in ann['tel_list'])}")
        if ann.get("mail_list"):
            lines.append(f"Emails: {', '.join(str(x) for x in ann['mail_list'])}")
    else:
        lines.append("# DOCUMENT NON RECONNU")

    return "\n".join(lines)


class OpenAIOCRClient:
    """Client OCR basé sur OpenAI Vision et Structured Outputs (JSON Schema)."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_OCR_MODEL or "gpt-6-luna"
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            api_key = self.api_key or settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self._client = AsyncOpenAI(api_key=api_key)
        return self._client

    def _convert_to_image_bytes(self, data: bytes) -> tuple[bytes, str]:
        """Convertit un document (PDF ou image) en octets JPEG optimisés pour la vision LLM."""
        if data.startswith(b"%PDF"):
            images = convert_from_bytes(data, dpi=200, fmt="png")
            if not images:
                raise ValueError("Le document PDF ne contient aucune page.")
            img = ImageOps.exif_transpose(images[0])
        else:
            img = Image.open(io.BytesIO(data))
            img = ImageOps.exif_transpose(img)

        # Si l'image a de la transparence (RGBA ou LA), fond blanc pour le JPEG
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90, optimize=True)
        return buf.getvalue(), "image/jpeg"

    async def process_pdf_annotations(self, pdf_bytes: bytes) -> dict[str, Any]:
        """
        Extrait un JSON structuré selon le schéma DocumentAnnotation (JSON Schema OpenAI)
        à partir d'un PDF ou d'une image de page.
        """
        img_bytes, mime_type = await asyncio.to_thread(self._convert_to_image_bytes, pdf_bytes)
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{img_base64}"

        system_prompt = (
            "Tu es un expert mondial en lecture et transcription OCR de documents manuscrits pour Le Studio des Parfums.\n"
            "Analyse avec une très grande précision l'image du document et extrais l'ensemble des données selon le schéma JSON fourni.\n\n"
            "Règles strictes :\n"
            "1. Classification :\n"
            "   - 'studio_parfums' s'il s'agit d'une fiche client / création de parfum (avec coordonnées et tableaux de notes de parfum).\n"
            "   - 'blank_sheet' s'il s'agit d'une feuille statistique (avec mois/année, listes de numéros manquants, doublons, téléphones, emails).\n"
            "   - 'unknown' si le document ne correspond à aucun de ces deux types.\n"
            "2. Fiche Studio des Parfums :\n"
            "   - 'identifiant' : le numéro de création manuscrit (généralement 8 à 10 chiffres, commençant souvent par 20 ou 82...). Ne pas inventer de chiffres.\n"
            "   - 'genre' : la civilité cochée (Mr, Mme, Mlle, Ms). Ne pas déduire du prénom.\n"
            "   - 'nom', 'prenom', 'date', 'ville', 'pays', 'tel', 'email', 'profession', 'date_naissance', 'groupe' : transcrire fidèlement ce qui est écrit.\n"
            "   - Pour l'email, sois très vigilant sur l'orthographe manuscrite, l'arobase et le nom de domaine.\n"
            "   - Pour les tableaux 'notes_de_tete', 'notes_de_coeur', 'notes_de_fond' : extraire chaque essence manuscrite dans 'essence' et sa quantité manuscrite en ml dans 'quantite_ml' (ex: '1', '2', '1+1', '0.5'). Ignorer les en-têtes et textes imprimés.\n"
            "3. Tout champ illisible ou non renseigné doit être null."
        )

        user_content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": "Transcris et extrais précisément l'intégralité des informations de cette fiche selon le schéma JSON.",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url,
                    "detail": "high",
                },
            },
        ]

        logger.info(f"[OpenAI OCR] Envoi de l'image ({len(img_bytes)} bytes) au modèle {self.model} avec JSON schema")

        usage_info = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        try:
            completion = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format=DocumentAnnotation,
            )

            if hasattr(completion, "usage") and completion.usage:
                usage_info["prompt_tokens"] = completion.usage.prompt_tokens or 0
                usage_info["completion_tokens"] = completion.usage.completion_tokens or 0
                usage_info["total_tokens"] = completion.usage.total_tokens or 0

            parsed_message = completion.choices[0].message
            if getattr(parsed_message, "refusal", None):
                raise ValueError(f"Le modèle a refusé la requête: {parsed_message.refusal}")

            annotation: DocumentAnnotation = parsed_message.parsed
            ann_dict = annotation.model_dump()
        except Exception as e:
            logger.warning(f"[OpenAI OCR] Échec via beta.chat.completions.parse: {e}. Tentative via json_object standard...")
            # Fallback en JSON standard si beta.parse échoue
            fallback_response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt + "\nRéponds exclusivement avec un objet JSON valide conforme aux champs demandés.",
                    },
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            if hasattr(fallback_response, "usage") and fallback_response.usage:
                usage_info["prompt_tokens"] = fallback_response.usage.prompt_tokens or 0
                usage_info["completion_tokens"] = fallback_response.usage.completion_tokens or 0
                usage_info["total_tokens"] = fallback_response.usage.total_tokens or 0

            content = fallback_response.choices[0].message.content or "{}"
            ann_dict = json.loads(content)

        markdown_text = _generate_markdown_from_annotation(ann_dict)

        logger.info(
            f"[OpenAI OCR] Extraction réussie — type={ann_dict.get('document_type')}, "
            f"identifiant={ann_dict.get('identifiant')}, client={ann_dict.get('nom')} {ann_dict.get('prenom')}"
        )

        return {
            "document_annotation": ann_dict,
            "usage": usage_info,
            "pages": [
                {
                    "markdown": markdown_text,
                    "tables": [],
                }
            ],
        }

    async def process_pdf_ocr(self, pdf_bytes: bytes) -> dict[str, Any]:
        """OCR général d'une page PDF ou d'une image, renvoyant le texte au format markdown."""
        img_bytes, mime_type = await asyncio.to_thread(self._convert_to_image_bytes, pdf_bytes)
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{img_base64}"

        logger.info(f"[OpenAI OCR] Transcription markdown brute avec {self.model}")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en OCR de fiches manuscrites pour Le Studio des Parfums. "
                        "Transcris fidèlement l'intégralité du texte manuscrit et imprimé en markdown, "
                        "en restituant les tableaux sous forme de tables markdown bien formatées."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transcris ce document en markdown."},
                        {"type": "image_url", "image_url": {"url": image_data_url, "detail": "high"}},
                    ],
                },
            ],
        )

        raw_text = response.choices[0].message.content or ""

        return {
            "pages": [
                {
                    "markdown": raw_text,
                    "tables": [],
                }
            ]
        }

    async def process_image_ocr(self, image_bytes: bytes) -> str:
        """OCR direct d'une image renvoyant le texte brut."""
        data = await self.process_pdf_ocr(image_bytes)
        pages = data.get("pages", [])
        if pages:
            return pages[0].get("markdown", "")
        return ""


openai_ocr_client = OpenAIOCRClient()
