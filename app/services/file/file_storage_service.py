import os
import shutil
import re
from typing import Optional, Tuple, List
from datetime import datetime
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps
import io
import boto3
from botocore.exceptions import ClientError


# Mode de stockage : "local" ou "s3"
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")


def _get_s3_client():
    endpoint = os.getenv("AWS_S3_ENDPOINT")  # optionnel (R2, MinIO, etc.)
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_S3_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=endpoint or None,
    )


S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")


class FileStorageService:
    """
    Service de stockage de fichiers.
    Mode local (défaut) ou S3/R2 selon STORAGE_BACKEND=s3.
    Les chemins stockés en BDD sont identiques dans les deux modes.
    """

    BASE_STORAGE_DIR = "files"
    CUSTOMERS_DIR = "customers"
    PENDING_DIR = "pending"

    def __init__(self):
        if STORAGE_BACKEND != "s3":
            self._ensure_base_directories()
        else:
            print(f"📦 Stockage S3 activé — bucket: {S3_BUCKET}")

    # ------------------------------------------------------------------
    # Utilitaires internes
    # ------------------------------------------------------------------

    def _ensure_base_directories(self):
        os.makedirs(os.path.join(self.BASE_STORAGE_DIR, self.CUSTOMERS_DIR), exist_ok=True)
        os.makedirs(os.path.join(self.BASE_STORAGE_DIR, self.PENDING_DIR), exist_ok=True)

    def _generate_filename(self, original_filename: str) -> str:
        timestamp = int(datetime.now().timestamp())
        clean_name = original_filename.replace(" ", "_")
        return f"{timestamp}_{clean_name}"

    def _s3_key(self, relative_path: str) -> str:
        """Normalise le séparateur pour S3 (toujours '/')"""
        return relative_path.replace(os.sep, "/")

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------

    def _write(self, relative_path: str, file_bytes: bytes) -> None:
        if STORAGE_BACKEND == "s3":
            _get_s3_client().put_object(
                Bucket=S3_BUCKET,
                Key=self._s3_key(relative_path),
                Body=file_bytes,
            )
        else:
            full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file_bytes)

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def get_file_bytes(self, relative_path: str) -> Optional[bytes]:
        try:
            if STORAGE_BACKEND == "s3":
                response = _get_s3_client().get_object(
                    Bucket=S3_BUCKET,
                    Key=self._s3_key(relative_path),
                )
                return response["Body"].read()
            else:
                full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)
                if os.path.exists(full_path):
                    with open(full_path, "rb") as f:
                        return f.read()
                return None
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            print(f"❌ Erreur lecture S3: {e}")
            return None
        except Exception as e:
            print(f"❌ Erreur lecture fichier: {e}")
            return None

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def delete_file(self, relative_path: str) -> bool:
        try:
            if STORAGE_BACKEND == "s3":
                _get_s3_client().delete_object(
                    Bucket=S3_BUCKET,
                    Key=self._s3_key(relative_path),
                )
            else:
                full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            print(f"🗑️ Fichier supprimé: {relative_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur suppression fichier: {e}")
            return False

    # ------------------------------------------------------------------
    # Sauvegarde
    # ------------------------------------------------------------------

    def save_file_temporary(self, file_bytes: bytes, original_filename: str) -> Tuple[str, str]:
        filename = self._generate_filename(original_filename)
        relative_path = f"{self.PENDING_DIR}/{filename}"
        self._write(relative_path, file_bytes)
        print(f"📁 Fichier sauvegardé temporairement: {relative_path}")
        return relative_path, filename

    def save_file_for_customer(
        self,
        file_bytes: bytes,
        customer_id: int,
        original_filename: str,
    ) -> Tuple[str, str]:
        filename = self._generate_filename(original_filename)
        relative_path = f"{self.CUSTOMERS_DIR}/{customer_id}/{filename}"
        self._write(relative_path, file_bytes)
        print(f"📁 Fichier sauvegardé pour customer {customer_id}: {relative_path}")
        return relative_path, filename

    def move_file_to_customer(self, temp_relative_path: str, customer_id: int) -> str:
        filename = os.path.basename(temp_relative_path)
        new_relative_path = f"{self.CUSTOMERS_DIR}/{customer_id}/{filename}"

        if STORAGE_BACKEND == "s3":
            s3 = _get_s3_client()
            s3.copy_object(
                Bucket=S3_BUCKET,
                CopySource={"Bucket": S3_BUCKET, "Key": self._s3_key(temp_relative_path)},
                Key=self._s3_key(new_relative_path),
            )
            s3.delete_object(Bucket=S3_BUCKET, Key=self._s3_key(temp_relative_path))
        else:
            temp_full_path = os.path.join(self.BASE_STORAGE_DIR, temp_relative_path)
            if not os.path.exists(temp_full_path):
                raise FileNotFoundError(f"Fichier temporaire non trouvé: {temp_full_path}")
            new_full_path = os.path.join(self.BASE_STORAGE_DIR, new_relative_path)
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            shutil.move(temp_full_path, new_full_path)

        print(f"📦 Fichier déplacé: {temp_relative_path} → {new_relative_path}")
        return new_relative_path

    # ------------------------------------------------------------------
    # Conversion PDF → images
    # ------------------------------------------------------------------

    def convert_pdf_to_images(self, pdf_bytes: bytes, dpi: int = 200) -> List[Tuple[bytes, str]]:
        try:
            images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt="png")
            result = []
            for i, image in enumerate(images):
                # Correction automatique rotation EXIF
                image = ImageOps.exif_transpose(image)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                result.append((buf.getvalue(), "png"))
                print(f"🖼️ Page {i+1}/{len(images)} convertie en image PNG")
            return result
        except Exception as e:
            print(f"❌ Erreur conversion PDF → Image: {e}")
            raise

    def save_pdf_and_images(
        self,
        pdf_bytes: bytes,
        customer_id: Optional[int],
        original_filename: str,
    ) -> Tuple[str, List[str]]:
        if customer_id is not None:
            pdf_path, pdf_filename = self.save_file_for_customer(pdf_bytes, customer_id, original_filename)
            base_prefix = f"{self.CUSTOMERS_DIR}/{customer_id}"
        else:
            pdf_path, pdf_filename = self.save_file_temporary(pdf_bytes, original_filename)
            base_prefix = self.PENDING_DIR

        images = self.convert_pdf_to_images(pdf_bytes)
        image_paths = []
        base_filename = os.path.splitext(pdf_filename)[0]

        for i, (img_bytes, ext) in enumerate(images):
            img_filename = f"{base_filename}_page_{i+1}.{ext}"
            img_relative_path = f"{base_prefix}/{img_filename}"
            self._write(img_relative_path, img_bytes)
            image_paths.append(img_relative_path)

        print(f"✅ PDF + {len(image_paths)} images sauvegardées")
        return pdf_path, image_paths

    # ------------------------------------------------------------------
    # Rotation manuelle (demandée par le front)
    # ------------------------------------------------------------------

    def rotate_image(self, relative_path: str, degrees: int) -> bool:
        if degrees % 90 != 0:
            raise ValueError("L'angle doit être un multiple de 90")
        try:
            file_bytes = self.get_file_bytes(relative_path)
            if not file_bytes:
                return False
            image = Image.open(io.BytesIO(file_bytes))
            rotated = image.rotate(-degrees, expand=True)
            buf = io.BytesIO()
            rotated.save(buf, format="PNG")
            self._write(relative_path, buf.getvalue())
            print(f"🔄 Image tournée de {degrees}°: {relative_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur rotation image: {e}")
            return False

    # ------------------------------------------------------------------
    # Utilitaires lecture
    # ------------------------------------------------------------------

    def get_pdf_path_from_image(self, image_relative_path: str) -> Optional[str]:
        try:
            directory = "/".join(image_relative_path.replace("\\", "/").split("/")[:-1])
            filename = os.path.basename(image_relative_path)
            match = re.match(r"(.+)_page_\d+\.\w+$", filename)
            if match:
                pdf_relative_path = f"{directory}/{match.group(1)}.pdf"
                # Vérifier existence
                if STORAGE_BACKEND == "s3":
                    try:
                        _get_s3_client().head_object(Bucket=S3_BUCKET, Key=self._s3_key(pdf_relative_path))
                        return pdf_relative_path
                    except ClientError:
                        return None
                else:
                    full_path = os.path.join(self.BASE_STORAGE_DIR, pdf_relative_path)
                    if os.path.exists(full_path):
                        return pdf_relative_path
            return None
        except Exception as e:
            print(f"❌ Erreur recherche PDF: {e}")
            return None

    def get_pdf_thumbnail(self, relative_path: str, dpi: int = 150) -> Optional[bytes]:
        try:
            pdf_bytes = self.get_file_bytes(relative_path)
            if not pdf_bytes:
                return None
            images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt="png", first_page=1, last_page=1)
            if not images:
                return None
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            print(f"🖼️ Miniature générée pour: {relative_path}")
            return buf.getvalue()
        except Exception as e:
            print(f"❌ Erreur génération miniature: {e}")
            return None


file_storage_service = FileStorageService()
