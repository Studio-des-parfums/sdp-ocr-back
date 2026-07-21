from fastapi import APIRouter, HTTPException

from app.schemas.tablet_schemas import (
    NoteCatalogItem,
    NotesCatalogResponse,
    TabletSubmissionCreate,
    TabletSubmissionResponse,
)
from app.repositories.tablet_submission_repository import tablet_submission_repository
from app.utils.note_corrector import NoteCorrector

router = APIRouter()


@router.get("/notes", response_model=NotesCatalogResponse)
async def get_notes_catalog():
    """
    Référentiel des notes disponibles pour la composition sur tablette,
    groupées par type (tête / cœur / fond).
    """
    def _items(category: str):
        return sorted(
            (
                NoteCatalogItem(code=code, name=name)
                for code, name in NoteCorrector.DATA[category].items()
            ),
            key=lambda item: item.name,
        )

    return NotesCatalogResponse(
        top_notes=_items("T"),
        heart_notes=_items("C"),
        base_notes=_items("F"),
    )


@router.post("/submissions", response_model=TabletSubmissionResponse)
async def create_tablet_submission(submission: TabletSubmissionCreate):
    """
    Enregistre une soumission du formulaire tablette :
    - retrouve le client par email (prioritaire) ou téléphone, sinon le crée
    - crée la formule (source 'tablet', sans fiche scannée) et ses notes
    """
    if not submission.top_notes and not submission.heart_notes and not submission.base_notes:
        raise HTTPException(status_code=422, detail="Au moins une note est requise")

    result, error = tablet_submission_repository.create_submission(submission)
    if error:
        raise HTTPException(status_code=500, detail=error)

    return TabletSubmissionResponse(**result)
