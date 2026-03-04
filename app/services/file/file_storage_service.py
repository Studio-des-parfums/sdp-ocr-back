import os
import shutil
from typing import Optional, Tuple, List
from datetime import datetime
from pathlib import Path
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps
import io


class FileStorageService:
    """
    Service pour gérer le stockage des fichiers et la conversion PDF → Image
    """

    # Répertoires de base
    BASE_STORAGE_DIR = "files"
    CUSTOMERS_DIR = "customers"
    PENDING_DIR = "pending"

    def __init__(self):
        """Initialise les répertoires de stockage"""
        self._ensure_base_directories()

    def _ensure_base_directories(self):
        """Crée les répertoires de base s'ils n'existent pas"""
        os.makedirs(os.path.join(self.BASE_STORAGE_DIR, self.CUSTOMERS_DIR), exist_ok=True)
        os.makedirs(os.path.join(self.BASE_STORAGE_DIR, self.PENDING_DIR), exist_ok=True)

    def _generate_filename(self, original_filename: str) -> str:
        """
        Génère un nom de fichier unique avec timestamp

        Args:
            original_filename: Nom original du fichier

        Returns:
            Nom de fichier au format: {timestamp}_{original_filename}
        """
        timestamp = int(datetime.now().timestamp())
        # Nettoyer le nom de fichier
        clean_name = original_filename.replace(" ", "_")
        return f"{timestamp}_{clean_name}"

    def save_file_temporary(self, file_bytes: bytes, original_filename: str) -> Tuple[str, str]:
        """
        Sauvegarde un fichier temporairement dans le dossier pending

        Args:
            file_bytes: Contenu du fichier
            original_filename: Nom original du fichier

        Returns:
            Tuple (chemin_relatif, nom_fichier)
        """
        filename = self._generate_filename(original_filename)
        relative_path = os.path.join(self.PENDING_DIR, filename)
        full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)

        # Sauvegarder le fichier
        with open(full_path, "wb") as f:
            f.write(file_bytes)

        print(f"📁 Fichier sauvegardé temporairement: {relative_path}")
        return relative_path, filename

    def save_file_for_customer(
        self,
        file_bytes: bytes,
        customer_id: int,
        original_filename: str
    ) -> Tuple[str, str]:
        """
        Sauvegarde un fichier pour un customer spécifique

        Args:
            file_bytes: Contenu du fichier
            customer_id: ID du customer
            original_filename: Nom original du fichier

        Returns:
            Tuple (chemin_relatif, nom_fichier)
        """
        # Créer le dossier du customer s'il n'existe pas
        customer_dir = os.path.join(self.BASE_STORAGE_DIR, self.CUSTOMERS_DIR, str(customer_id))
        os.makedirs(customer_dir, exist_ok=True)

        filename = self._generate_filename(original_filename)
        relative_path = os.path.join(self.CUSTOMERS_DIR, str(customer_id), filename)
        full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)

        # Sauvegarder le fichier
        with open(full_path, "wb") as f:
            f.write(file_bytes)

        print(f"📁 Fichier sauvegardé pour customer {customer_id}: {relative_path}")
        return relative_path, filename

    def move_file_to_customer(self, temp_relative_path: str, customer_id: int) -> str:
        """
        Déplace un fichier du dossier pending vers le dossier d'un customer

        Args:
            temp_relative_path: Chemin relatif du fichier temporaire
            customer_id: ID du customer

        Returns:
            Nouveau chemin relatif du fichier
        """
        # Chemins source
        temp_full_path = os.path.join(self.BASE_STORAGE_DIR, temp_relative_path)

        if not os.path.exists(temp_full_path):
            raise FileNotFoundError(f"Fichier temporaire non trouvé: {temp_full_path}")

        # Créer le dossier du customer
        customer_dir = os.path.join(self.BASE_STORAGE_DIR, self.CUSTOMERS_DIR, str(customer_id))
        os.makedirs(customer_dir, exist_ok=True)

        # Nouveau chemin
        filename = os.path.basename(temp_relative_path)
        new_relative_path = os.path.join(self.CUSTOMERS_DIR, str(customer_id), filename)
        new_full_path = os.path.join(self.BASE_STORAGE_DIR, new_relative_path)

        # Déplacer le fichier
        shutil.move(temp_full_path, new_full_path)

        print(f"📦 Fichier déplacé: {temp_relative_path} → {new_relative_path}")
        return new_relative_path

    def convert_pdf_to_images(
        self,
        pdf_bytes: bytes,
        dpi: int = 200
    ) -> List[Tuple[bytes, str]]:
        """
        Convertit un PDF en images PNG (une image par page)

        Args:
            pdf_bytes: Contenu du PDF
            dpi: Résolution des images (défaut: 200)

        Returns:
            Liste de tuples (image_bytes, extension) pour chaque page
        """
        try:
            # Convertir le PDF en images (poppler applique déjà le /Rotate PDF)
            images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='png')

            result = []
            for i, image in enumerate(images):
                # Corriger automatiquement la rotation EXIF (scans/photos embarqués)
                image = ImageOps.exif_transpose(image)

                # Convertir l'image PIL en bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()

                result.append((img_bytes, 'png'))
                print(f"🖼️ Page {i+1}/{len(images)} convertie en image PNG")

            return result

        except Exception as e:
            print(f"❌ Erreur conversion PDF → Image: {e}")
            raise

    def save_pdf_and_images(
        self,
        pdf_bytes: bytes,
        customer_id: Optional[int],
        original_filename: str
    ) -> Tuple[str, List[str]]:
        """
        Sauvegarde un PDF et ses images converties

        Args:
            pdf_bytes: Contenu du PDF
            customer_id: ID du customer (None = pending)
            original_filename: Nom original du fichier

        Returns:
            Tuple (pdf_path, [image_paths])
        """
        # Sauvegarder le PDF
        if customer_id is not None:
            pdf_path, pdf_filename = self.save_file_for_customer(
                pdf_bytes, customer_id, original_filename
            )
            base_dir = os.path.join(self.BASE_STORAGE_DIR, self.CUSTOMERS_DIR, str(customer_id))
        else:
            pdf_path, pdf_filename = self.save_file_temporary(pdf_bytes, original_filename)
            base_dir = os.path.join(self.BASE_STORAGE_DIR, self.PENDING_DIR)

        # Convertir en images
        images = self.convert_pdf_to_images(pdf_bytes)

        # Sauvegarder chaque image
        image_paths = []
        base_filename = os.path.splitext(pdf_filename)[0]

        for i, (img_bytes, ext) in enumerate(images):
            img_filename = f"{base_filename}_page_{i+1}.{ext}"
            img_full_path = os.path.join(base_dir, img_filename)

            with open(img_full_path, "wb") as f:
                f.write(img_bytes)

            # Chemin relatif
            if customer_id is not None:
                img_relative_path = os.path.join(self.CUSTOMERS_DIR, str(customer_id), img_filename)
            else:
                img_relative_path = os.path.join(self.PENDING_DIR, img_filename)

            image_paths.append(img_relative_path)

        print(f"✅ PDF + {len(image_paths)} images sauvegardées")
        return pdf_path, image_paths

    def delete_file(self, relative_path: str) -> bool:
        """
        Supprime un fichier

        Args:
            relative_path: Chemin relatif du fichier

        Returns:
            True si succès, False sinon
        """
        try:
            full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"🗑️ Fichier supprimé: {relative_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur suppression fichier: {e}")
            return False

    def get_file_bytes(self, relative_path: str) -> Optional[bytes]:
        """
        Récupère le contenu d'un fichier

        Args:
            relative_path: Chemin relatif du fichier

        Returns:
            Contenu du fichier ou None
        """
        try:
            full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"❌ Erreur lecture fichier: {e}")
            return None

    def get_pdf_path_from_image(self, image_relative_path: str) -> Optional[str]:
        """
        Trouve le chemin du PDF correspondant à une image convertie

        L'image a le format: {timestamp}_{filename}_page_{n}.png
        Le PDF a le format: {timestamp}_{filename}.pdf

        Args:
            image_relative_path: Chemin relatif de l'image

        Returns:
            Chemin relatif du PDF ou None si non trouvé
        """
        try:
            # Extraire le répertoire et le nom de fichier
            directory = os.path.dirname(image_relative_path)
            filename = os.path.basename(image_relative_path)

            # Retirer le suffixe _page_N.png pour obtenir le nom du PDF
            # Pattern: {timestamp}_{original}_page_{n}.png -> {timestamp}_{original}.pdf
            import re
            match = re.match(r'(.+)_page_\d+\.\w+$', filename)

            if match:
                base_name = match.group(1)
                pdf_filename = f"{base_name}.pdf"
                pdf_relative_path = os.path.join(directory, pdf_filename)

                # Vérifier que le PDF existe
                full_path = os.path.join(self.BASE_STORAGE_DIR, pdf_relative_path)
                if os.path.exists(full_path):
                    return pdf_relative_path

            return None

        except Exception as e:
            print(f"❌ Erreur recherche PDF: {e}")
            return None

    def rotate_image(self, relative_path: str, degrees: int) -> bool:
        """
        Tourne physiquement une image et écrase le fichier stocké.

        Args:
            relative_path: Chemin relatif de l'image
            degrees: Angle de rotation (90, 180, 270)

        Returns:
            True si succès, False sinon
        """
        if degrees % 90 != 0:
            raise ValueError("L'angle doit être un multiple de 90")

        try:
            full_path = os.path.join(self.BASE_STORAGE_DIR, relative_path)
            if not os.path.exists(full_path):
                return False

            image = Image.open(full_path)
            # expand=True pour que les rotations 90/270 conservent les bonnes dimensions
            rotated = image.rotate(-degrees, expand=True)
            rotated.save(full_path)

            print(f"🔄 Image tournée de {degrees}°: {relative_path}")
            return True

        except Exception as e:
            print(f"❌ Erreur rotation image: {e}")
            return False

    def get_pdf_thumbnail(self, relative_path: str, dpi: int = 150) -> Optional[bytes]:
        """
        Génère une miniature de la première page d'un PDF

        Args:
            relative_path: Chemin relatif du PDF
            dpi: Résolution de la miniature (défaut: 150)

        Returns:
            Image PNG de la première page ou None
        """
        try:
            # Lire le PDF
            pdf_bytes = self.get_file_bytes(relative_path)
            if not pdf_bytes:
                return None

            # Convertir seulement la première page
            images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='png', first_page=1, last_page=1)

            if not images:
                return None

            # Convertir l'image PIL en bytes
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            print(f"🖼️ Miniature générée pour: {relative_path}")
            return img_bytes

        except Exception as e:
            print(f"❌ Erreur génération miniature: {e}")
            return None


file_storage_service = FileStorageService()
