import re
import os
import traceback
import urllib.parse

from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from fastapi.responses import Response
from typing import Optional

from app.repositories.customer_file_repository import customer_file_repository
from app.services.file import file_storage_service
from app.schemas.customer_file_schemas import CustomerFileResponse, CustomerFileListResponse
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/customers/{customer_id}/files", response_model=CustomerFileListResponse)
async def get_customer_files(customer_id: int):
    """
    Récupère tous les fichiers d'un customer
    """
    try:
        files = customer_file_repository.get_files_by_customer_id(customer_id)

        file_responses = [CustomerFileResponse(**file) for file in files]

        return CustomerFileListResponse(
            files=file_responses,
            total=len(file_responses)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/customer-reviews/{customer_review_id}/files", response_model=CustomerFileListResponse)
async def get_customer_review_files(customer_review_id: int):
    """
    Récupère tous les fichiers d'un customer_review
    """
    try:
        files = customer_file_repository.get_files_by_customer_review_id(customer_review_id)

        file_responses = [CustomerFileResponse(**file) for file in files]

        return CustomerFileListResponse(
            files=file_responses,
            total=len(file_responses)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/files/{file_id}")
async def get_file(file_id: int):
    """
    Récupère les informations d'un fichier
    """
    try:
        file = customer_file_repository.get_customer_file_by_id(file_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Fichier avec ID {file_id} non trouvé"
            )

        return CustomerFileResponse(**file)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/files/{file_id}/content")
async def get_file_content(file_id: int):
    """
    Télécharge le contenu d'un fichier (PDF ou Image)
    """
    try:
        # Récupérer les informations du fichier
        file = customer_file_repository.get_customer_file_by_id(file_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Fichier avec ID {file_id} non trouvé"
            )

        # Récupérer le contenu du fichier
        file_bytes = file_storage_service.get_file_bytes(file['file_path'])

        if not file_bytes:
            raise HTTPException(
                status_code=404,
                detail=f"Contenu du fichier non trouvé: {file['file_path']}"
            )

        # Déterminer le media type
        media_type = file.get('file_type', 'application/octet-stream')

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f"inline; filename*=UTF-8''{urllib.parse.quote(file['file_name'])}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur get_file_content file_id={file_id}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/files/restore-bulk")
async def restore_bulk(zip_file: UploadFile = File(...)):
    """
    Restaure tous les fichiers en masse depuis un ZIP de PDFs multi-pages originaux.

    Format attendu des fichiers dans le ZIP : "202512 de 001 à 005.pdf"
    Format en BDD : "1771856562_page_1_202512_de_001_à_005.pdf"

    Pour chaque PDF dans le ZIP :
    1. Normalise le nom (espaces → underscores, sans extension)
    2. Découpe le PDF page par page
    3. Pour chaque page i, cherche en BDD le fichier dont le nom correspond
       au pattern `*_page_{i}_{nom_normalisé}.pdf`
    4. Écrit le PDF de la page au file_path BDD dans S3
    5. Régénère l'image PNG associée
    """
    import zipfile
    import io as _io
    import unicodedata
    from app.utils.pdf_splitter import pdf_splitter

    def fix_zip_filename(name: str) -> str:
        """Corrige les noms de fichiers macOS mal décodés (CP437 au lieu d'UTF-8)"""
        try:
            # macOS stocke en UTF-8 NFD sans flag UTF-8 → Python lit en CP437
            # On annule : NFC → encode CP437 → decode UTF-8
            return unicodedata.normalize('NFC', name).encode('cp437').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            return name

    def normalize(s: str) -> str:
        """NFD + espaces→underscores pour comparaison uniforme"""
        return unicodedata.normalize('NFD', s).replace(' ', '_')

    try:
        zip_bytes = await zip_file.read()
        zip_buf = _io.BytesIO(zip_bytes)

        if not zipfile.is_zipfile(zip_buf):
            raise HTTPException(status_code=400, detail="Le fichier envoyé n'est pas un ZIP valide")

        # Construire l'index BDD : (nom_original_normalisé, page_num) → db_record
        # Index PDF : (nom_original_normalisé, page_num) → db_record
        # file_name format en BDD : "{timestamp}_page_{page}_{original_name}.pdf"
        all_pdfs = customer_file_repository.get_all_pdf_files()
        db_index = {}
        pattern = re.compile(r'^\d+_page_(\d+)_(.+)\.pdf$')
        for row in all_pdfs:
            m = pattern.match(row['file_name'])
            if m:
                page_num = int(m.group(1))
                original_name = normalize(m.group(2))
                db_index[(original_name, page_num)] = row

        # Index images : file_name (sans extension) → db_record
        # file_name format en BDD : "{pdf_basename}_page_1.png"
        all_images = customer_file_repository.get_all_image_files()
        img_index = {os.path.splitext(row['file_name'])[0]: row for row in all_images}

        print(f"📋 Index BDD — {len(db_index)} PDFs, {len(img_index)} images")

        restored, skipped, errors = [], [], []

        zip_buf.seek(0)
        with zipfile.ZipFile(zip_buf, 'r') as zf:
            pdf_entries = [
                n for n in zf.namelist()
                if n.lower().endswith('.pdf') and not os.path.basename(n).startswith('._')
            ]
            print(f"📦 ZIP reçu — {len(pdf_entries)} PDFs originaux à traiter")

            for entry in pdf_entries:
                filename = fix_zip_filename(os.path.basename(entry))
                if not filename:
                    continue

                # Normaliser le nom : NFD + espaces→underscores, retirer .pdf
                normalized_name = normalize(os.path.splitext(filename)[0])
                print(f"🔍 ZIP clé: {repr(normalized_name)} bytes={normalized_name.encode('utf-8')}")

                try:
                    pdf_bytes_orig = zf.read(entry)

                    # Découper le PDF page par page
                    pages = pdf_splitter.split_pdf_to_pages(pdf_bytes_orig)
                    print(f"   {len(pages)} page(s) extraite(s)")

                    for i, page_pdf_bytes in enumerate(pages):
                        page_num = i + 1
                        key = (normalized_name, page_num)
                        db_file = db_index.get(key)

                        if not db_file:
                            skipped.append(f"{filename} page {page_num}")
                            print(f"   ⚠️ Page {page_num} — aucune correspondance en BDD pour clé {key}")
                            continue

                        file_path = db_file['file_path']
                        try:
                            # Écrire le PDF de la page au chemin BDD
                            file_storage_service._write(file_path, page_pdf_bytes)
                            customer_file_repository.update_customer_file(db_file['id'], {'new_url': True})

                            # Régénérer l'image PNG et écrire au chemin BDD de l'image
                            images = file_storage_service.convert_pdf_to_images(page_pdf_bytes)
                            pdf_basename = os.path.splitext(db_file['file_name'])[0]
                            for j, (img_bytes, ext) in enumerate(images):
                                img_key = f"{pdf_basename}_page_{j+1}"
                                img_db = img_index.get(img_key)
                                if img_db:
                                    file_storage_service._write(img_db['file_path'], img_bytes)
                                    customer_file_repository.update_customer_file(img_db['id'], {'new_url': True})
                                    print(f"   🖼️ Image restaurée → {img_db['file_path']}")
                                else:
                                    # Fallback : écrire au chemin dérivé du PDF
                                    base = os.path.splitext(file_path)[0]
                                    file_storage_service._write(f"{base}_page_{j+1}.{ext}", img_bytes)

                            restored.append(file_path)
                            print(f"   ✅ Page {page_num} restaurée → {file_path}")

                        except Exception as e:
                            errors.append({"file": f"{filename} page {page_num}", "error": str(e)})
                            print(f"   ❌ Erreur page {page_num}: {e}")

                except Exception as e:
                    errors.append({"file": filename, "error": str(e)})
                    print(f"❌ Erreur sur {filename}: {e}")

        return {
            "success": True,
            "restored": len(restored),
            "skipped": len(skipped),
            "errors": len(errors),
            "error_details": errors,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/files/{file_id}/restore")
async def restore_file(file_id: int, file: UploadFile = File(...)):
    """
    Re-uploade un fichier manquant vers S3 en utilisant le chemin déjà enregistré en BDD.
    Utile pour restaurer les fichiers perdus avant la migration S3.
    Si c'est un PDF, régénère aussi l'image associée.
    """
    try:
        db_file = customer_file_repository.get_customer_file_by_id(file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail=f"Fichier {file_id} non trouvé en BDD")

        file_bytes = await file.read()
        file_path = db_file['file_path']

        # Écrire directement au chemin enregistré en BDD
        file_storage_service._write(file_path, file_bytes)

        # Si c'est un PDF, régénérer l'image associée
        regenerated_images = []
        if db_file.get('file_type') == 'application/pdf':
            try:
                images = file_storage_service.convert_pdf_to_images(file_bytes)
                base = os.path.splitext(file_path)[0]
                for i, (img_bytes, ext) in enumerate(images):
                    img_path = f"{base}_page_{i+1}.{ext}"
                    file_storage_service._write(img_path, img_bytes)
                    regenerated_images.append(img_path)
            except Exception as e:
                print(f"⚠️ Impossible de régénérer l'image: {e}")

        return {
            "success": True,
            "file_id": file_id,
            "restored_path": file_path,
            "regenerated_images": regenerated_images,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/files/{file_id}/download")
async def download_file(file_id: int):
    """
    Force le téléchargement du PDF associé au fichier
    Si le fichier est une image issue d'un PDF, télécharge le PDF source
    """
    try:
        # Récupérer les informations du fichier
        file = customer_file_repository.get_customer_file_by_id(file_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Fichier avec ID {file_id} non trouvé"
            )

        file_path = file['file_path']
        file_name = file['file_name']
        media_type = 'application/pdf'

        # Si c'est une image, chercher le PDF correspondant
        if file.get('file_type', '').startswith('image/'):
            pdf_path = file_storage_service.get_pdf_path_from_image(file_path)
            if pdf_path:
                file_path = pdf_path
                # Générer le nom du PDF à partir du nom de l'image
                match = re.match(r'(.+)_page_\d+\.\w+$', file_name)
                if match:
                    file_name = f"{match.group(1)}.pdf"
                else:
                    file_name = file_name.rsplit('.', 1)[0] + '.pdf'

        # Récupérer le contenu du fichier
        file_bytes = file_storage_service.get_file_bytes(file_path)

        if not file_bytes:
            raise HTTPException(
                status_code=404,
                detail=f"Contenu du fichier non trouvé: {file_path}"
            )

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{urllib.parse.quote(file_name)}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/formulas/{formula_id}/file", response_model=CustomerFileResponse)
async def get_formula_file(formula_id: int):
    """
    Récupère les informations du fichier associé à une formule
    """
    try:
        file = customer_file_repository.get_file_by_formula_id(formula_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun fichier trouvé pour la formule {formula_id}"
            )

        return CustomerFileResponse(**file)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/formulas/{formula_id}/file/content")
async def get_formula_file_content(formula_id: int):
    """
    Récupère le contenu du fichier associé à une formule (pour affichage)
    """
    try:
        file = customer_file_repository.get_file_by_formula_id(formula_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun fichier trouvé pour la formule {formula_id}"
            )

        # Récupérer le contenu du fichier
        file_bytes = file_storage_service.get_file_bytes(file['file_path'])

        if not file_bytes:
            raise HTTPException(
                status_code=404,
                detail=f"Contenu du fichier non trouvé: {file['file_path']}"
            )

        # Déterminer le media type
        media_type = file.get('file_type', 'application/octet-stream')

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f"inline; filename*=UTF-8''{urllib.parse.quote(file['file_name'])}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/formulas/{formula_id}/file/thumbnail")
async def get_formula_file_thumbnail(formula_id: int):
    """
    Récupère une miniature (première page) du fichier PDF associé à une formule
    Si le fichier est une image, retourne l'image directement
    """
    try:
        file = customer_file_repository.get_file_by_formula_id(formula_id)

        if not file:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun fichier trouvé pour la formule {formula_id}"
            )

        # Si c'est une image, retourner directement
        if file.get('file_type', '').startswith('image/'):
            file_bytes = file_storage_service.get_file_bytes(file['file_path'])

            if not file_bytes:
                raise HTTPException(
                    status_code=404,
                    detail=f"Contenu du fichier non trouvé: {file['file_path']}"
                )

            return Response(
                content=file_bytes,
                media_type=file.get('file_type', 'image/jpeg'),
                headers={
                    'Content-Disposition': f"inline; filename*=UTF-8''{urllib.parse.quote(file['file_name'])}"
                }
            )

        # Si c'est un PDF, générer une miniature
        if file.get('file_type') == 'application/pdf':
            thumbnail_bytes = file_storage_service.get_pdf_thumbnail(file['file_path'])

            if not thumbnail_bytes:
                raise HTTPException(
                    status_code=500,
                    detail="Erreur lors de la génération de la miniature"
                )

            return Response(
                content=thumbnail_bytes,
                media_type='image/png',
                headers={
                    'Content-Disposition': f"inline; filename*=UTF-8''thumbnail_{urllib.parse.quote(file['file_name'])}.png"
                }
            )

        # Type de fichier non supporté
        raise HTTPException(
            status_code=400,
            detail="Type de fichier non supporté pour la génération de miniature"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
