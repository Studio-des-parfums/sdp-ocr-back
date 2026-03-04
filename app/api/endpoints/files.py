import re
import os

from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from fastapi.responses import Response
from typing import Optional

from app.repositories.customer_file_repository import customer_file_repository
from app.services.file import file_storage_service
from app.schemas.customer_file_schemas import CustomerFileResponse, CustomerFileListResponse

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
                'Content-Disposition': f'inline; filename="{file["file_name"]}"'
            }
        )

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
                'Content-Disposition': f'attachment; filename="{file_name}"'
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
                'Content-Disposition': f'inline; filename="{file["file_name"]}"'
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
                    'Content-Disposition': f'inline; filename="{file["file_name"]}"'
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
                    'Content-Disposition': f'inline; filename="thumbnail_{file["file_name"]}.png"'
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
