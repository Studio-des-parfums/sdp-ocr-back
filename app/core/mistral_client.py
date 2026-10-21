import asyncio
import base64
import json

import requests

from app.core.config import settings
from app.schemas.ocr_schemas import MistralDocumentAnnotation

try:
    from mistralai import Mistral

    print("✅ Mistral SDK imported successfully")
except Exception as e:
    print(f"❌ Mistral SDK import failed: {type(e).__name__}: {e}")
    Mistral = None


class MistralOCRClient:
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        self.endpoint = "https://api.mistral.ai/v1/ocr"
        self._sdk_client = Mistral(api_key=self.api_key) if Mistral else None

    def _build_annotation_format(self) -> dict:
        """
        Construit un JSON schema pour document_annotation_format sans dépendre de mistralai.extra.
        Compatible Pydantic v1/v2 (schema() ou model_json_schema()).
        """
        try:
            schema = MistralDocumentAnnotation.schema()  # Pydantic v1
        except Exception:
            try:
                schema = MistralDocumentAnnotation.model_json_schema()  # Pydantic v2
            except Exception as e:
                raise RuntimeError(f"Cannot build JSON schema for annotations: {e}")

        return {
            "type": "json_schema",
            "json_schema": {
                "schema": schema,
                "name": "MistralDocumentAnnotation",
            },
        }

    def _encode_to_base64(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    async def process_image_ocr(self, image_bytes: bytes) -> str:
        """OCR image using direct API call."""
        image_base64 = self._encode_to_base64(image_bytes)

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:image/png;base64,{image_base64}",
            },
            "include_image_base64": False,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await asyncio.to_thread(
            requests.post, self.endpoint, headers=headers, json=payload, timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"OCR API error {response.status_code}: {response.text}")

        data = response.json()
        return data.get("text", "")

    async def process_pdf_ocr(self, pdf_bytes: bytes) -> dict:
        """OCR PDF using direct API call - returns full response with pages."""
        pdf_base64 = self._encode_to_base64(pdf_bytes)

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}",
            },
            "include_image_base64": False,
            "table_format": "markdown",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await asyncio.to_thread(
            requests.post, self.endpoint, headers=headers, json=payload, timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"OCR API error {response.status_code}: {response.text}")

        return response.json()

    async def process_pdf_annotations(self, pdf_bytes: bytes) -> dict:
        """
        Document AI - Annotations: demande un JSON structuré selon un schéma fourni.
        Le résultat structuré est dans `document_annotation`.
        """
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY non configurée.")

        pdf_base64 = self._encode_to_base64(pdf_bytes)
        document_url = (
            f"data:application/pdf;base64,{pdf_base64}"
            if pdf_bytes.startswith(b"%PDF")
            else f"data:image/png;base64,{pdf_base64}"
        )

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": document_url,
            },
            "include_image_base64": False,
            "table_format": "markdown",
            "document_annotation_format": self._build_annotation_format(),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await asyncio.to_thread(
            requests.post,
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=120,
        )

        if response.status_code != 200:
            raise Exception(f"OCR annotations API error {response.status_code}: {response.text}")

        data = response.json()

        try:
            if isinstance(data, dict):
                ann = (
                    data.get("document_annotation")
                    or data.get("document_annotations")
                    or data.get("annotation")
                )
                if isinstance(ann, str):
                    try:
                        ann_json = json.loads(ann)
                        if isinstance(ann_json, dict):
                            ann = ann_json
                    except Exception:
                        pass
                if isinstance(ann, dict):
                    data["document_annotation"] = ann
        except Exception:
            pass

        return data


mistral_ocr_client = MistralOCRClient()
