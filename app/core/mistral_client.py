import base64
import requests
import json
from app.core.config import settings

try:
    from mistralai import Mistral
    print("✅ Mistral SDK imported successfully")
except Exception as e:
    print(f"❌ Mistral SDK import failed: {type(e).__name__}: {e}")
    Mistral = None

from app.schemas.ocr_schemas import MistralDocumentAnnotation

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
        """
        OCR image using direct API call
        """
        image_base64 = self._encode_to_base64(image_bytes)

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:image/png;base64,{image_base64}"
            },
            "include_image_base64": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"OCR API error {response.status_code}: {response.text}")

        data = response.json()
        return data.get("text", "")

    async def process_pdf_ocr(self, pdf_bytes: bytes) -> dict:
        """
        OCR PDF using direct API call - returns full response with pages
        """
        pdf_base64 = self._encode_to_base64(pdf_bytes)
        print(f"PDF size: {len(pdf_bytes)} bytes, base64 size: {len(pdf_base64)}")

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}"
            },
            "include_image_base64": False,
            "table_format": "markdown"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=120
        )

        print(f"Mistral OCR response status: {response.status_code}")

        if response.status_code != 200:
            print(f"OCR API error: {response.text}")
            raise Exception(f"OCR API error {response.status_code}: {response.text}")

        data = response.json()
        
        # ⚠️ LOGS DE DIAGNOSTIC DÉTAILLÉS ⚠️
        print(f"\n{'='*80}")
        print(f"📋 RÉPONSE MISTRAL OCR COMPLÈTE:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])
        print(f"{'='*80}\n")
        
        if "pages" in data and len(data["pages"]) > 0:
            page_data = data["pages"][0]
            
            # Log du markdown
            markdown = page_data.get("markdown", "")
            print(f"📝 MARKDOWN EXTRAIT ({len(markdown)} caractères):")
            print(markdown[:2000])
            print(f"\n{'='*80}\n")
            
            # Vérifier si les tableaux sont dans un autre champ
            if "tables" in page_data:
                print(f"📊 TABLES TROUVÉES DANS page_data:")
                print(json.dumps(page_data["tables"], indent=2, ensure_ascii=False))
                print(f"{'='*80}\n")
            
            if "html" in page_data:
                print(f"📊 HTML TROUVÉ DANS page_data:")
                print(page_data["html"][:2000])
                print(f"{'='*80}\n")
            
            # Afficher toutes les clés disponibles dans page_data
            print(f"🔑 CLÉS DISPONIBLES DANS page_data: {list(page_data.keys())}")
            print(f"{'='*80}\n")
        
        # Vérifier au niveau racine aussi
        if "tables" in data:
            print(f"📊 TABLES TROUVÉES AU NIVEAU RACINE:")
            print(json.dumps(data["tables"], indent=2, ensure_ascii=False))
            print(f"{'='*80}\n")
        
        # Afficher toutes les clés au niveau racine
        print(f"🔑 CLÉS DISPONIBLES AU NIVEAU RACINE: {list(data.keys())}")
        print(f"{'='*80}\n")

        return data

    async def process_pdf_annotations(self, pdf_bytes: bytes) -> dict:
        """
        Document AI - Annotations: demande un JSON structuré selon un schéma fourni.

        Remarque: on fait une requête HTTP directe car le SDK 1.0.0 n'expose pas les chunks OCR.
        Le résultat structuré est dans `document_annotation`.
        """
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY non configurée.")

        pdf_base64 = self._encode_to_base64(pdf_bytes)
        document_url = f"data:application/pdf;base64,{pdf_base64}"

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

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=120,
        )

        if response.status_code != 200:
            print(f"Mistral Annotations response status: {response.status_code}")
            print(f"Mistral Annotations error: {response.text}")
            raise Exception(f"OCR annotations API error {response.status_code}: {response.text}")

        data = response.json()

        # ⚠️ LOGS DE DIAGNOSTIC DÉTAILLÉS ⚠️
        print(f"\n{'='*80}")
        print(f"📋 RÉPONSE MISTRAL ANNOTATIONS COMPLÈTE:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])
        print(f"{'='*80}\n")

        # Logs "safe": ne pas afficher de base64 ni de payload énorme
        try:
            if isinstance(data, dict):
                keys = list(data.keys())
                print(f"[MISTRAL][ANNOTATIONS] response keys: {keys}")
                ann = data.get("document_annotation") or data.get("document_annotations") or data.get("annotation")
                # Parfois l'API renvoie une chaîne JSON: on tente de la décoder.
                if isinstance(ann, str):
                    try:
                        ann_json = json.loads(ann)
                        if isinstance(ann_json, dict):
                            ann = ann_json
                    except Exception:
                        pass
                if isinstance(ann, dict):
                    print(f"[MISTRAL][ANNOTATIONS] document_annotation: {ann}")
                    data["document_annotation"] = ann  # normaliser en dict
                else:
                    print(f"[MISTRAL][ANNOTATIONS] document_annotation type: {type(ann)}")
        except Exception as _e:
            # On évite de casser le flux juste pour du logging
            pass

        # Vérifier les pages et le markdown pour les annotations aussi
        if "pages" in data and len(data["pages"]) > 0:
            page_data = data["pages"][0]
            
            # Log du markdown
            markdown = page_data.get("markdown", "")
            print(f"📝 MARKDOWN EXTRAIT (ANNOTATIONS) ({len(markdown)} caractères):")
            print(markdown[:2000])
            print(f"\n{'='*80}\n")
            
            # Vérifier si les tableaux sont dans un autre champ
            if "tables" in page_data:
                print(f"📊 TABLES TROUVÉES DANS page_data (ANNOTATIONS):")
                print(json.dumps(page_data["tables"], indent=2, ensure_ascii=False))
                print(f"{'='*80}\n")
            
            if "html" in page_data:
                print(f"📊 HTML TROUVÉ DANS page_data (ANNOTATIONS):")
                print(page_data["html"][:2000])
                print(f"{'='*80}\n")
            
            # Afficher toutes les clés disponibles dans page_data
            print(f"🔑 CLÉS DISPONIBLES DANS page_data (ANNOTATIONS): {list(page_data.keys())}")
            print(f"{'='*80}\n")
        
        # Vérifier au niveau racine aussi
        if "tables" in data:
            print(f"📊 TABLES TROUVÉES AU NIVEAU RACINE (ANNOTATIONS):")
            print(json.dumps(data["tables"], indent=2, ensure_ascii=False))
            print(f"{'='*80}\n")

        return data

mistral_ocr_client = MistralOCRClient()
