from fastapi import APIRouter, HTTPException

from app.database.connection import get_connection
from app.schemas.email_schemas import (
    EmailResponse,
    EmailTestRequest,
    PyramidPreviewResponse,
    PyramidRequest,
)
from app.services.email.email_sender_service import email_sender_service
from app.services.email.pyramid_email_service import (
    build_pyramid_html as _build_pyramid_html,
)
from app.services.email.pyramid_email_service import (
    get_pyramid_data as _get_pyramid_data_raw,
)
from app.services.email.pyramid_email_service import (
    send_pyramid_email_for_formula,
)

router = APIRouter()


def _get_pyramid_data(connection, reference=None, formula_id=None):
    """Wrapper HTTP : lève les HTTPException attendues par les routes de ce fichier."""
    if formula_id is None and not reference:
        raise HTTPException(status_code=422, detail="reference ou formula_id requis")

    data = _get_pyramid_data_raw(connection, reference=reference, formula_id=formula_id)
    if not data:
        raise HTTPException(status_code=404, detail="Formule ou client non trouve")

    return data


@router.post("/test", response_model=EmailResponse)
async def send_test_email(request: EmailTestRequest):
    try:
        result = email_sender_service.send_test_email(to_email=request.to_email)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pyramid/preview", response_model=PyramidPreviewResponse)
async def preview_pyramid_email(request: PyramidRequest):
    """Retourne le HTML de la pyramide pour prévisualisation sans envoyer l'email."""
    connection = None
    try:
        connection = get_connection()
        if not connection:
            raise HTTPException(status_code=500, detail="Erreur de connexion a la base de donnees")

        formula, customer, top_notes, heart_notes, base_notes, percentages = _get_pyramid_data(
            connection, reference=request.reference, formula_id=request.formula_id
        )

        subject = "Votre pyramide olfactive – Le Studio des Parfums"
        html = _build_pyramid_html(
            customer, formula, top_notes, heart_notes, base_notes, percentages, preview=True
        )

        return PyramidPreviewResponse(
            subject=subject,
            html=html,
            to_email=customer.get("email"),
            customer_name=f"{customer.get('last_name', '')} {customer.get('first_name', '')}".strip(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            connection.close()


@router.post("/pyramid", response_model=EmailResponse)
async def send_pyramid_email(request: PyramidRequest):
    connection = None
    try:
        connection = get_connection()
        if not connection:
            raise HTTPException(status_code=500, detail="Erreur de connexion a la base de donnees")

        if request.formula_id is None and not request.reference:
            raise HTTPException(status_code=422, detail="reference ou formula_id requis")

        formula_id = request.formula_id
        if formula_id is None:
            # _get_pyramid_data lève une 404 explicite si la référence n'existe pas
            formula, *_ = _get_pyramid_data(connection, reference=request.reference)
            formula_id = formula["id"]

        result = send_pyramid_email_for_formula(connection, formula_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            connection.close()
