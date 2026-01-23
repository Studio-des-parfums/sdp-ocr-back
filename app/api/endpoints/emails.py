from fastapi import APIRouter, HTTPException
from app.schemas.email_schemas import EmailSendRequest, EmailTestRequest, EmailResponse
from app.services.email.email_sender_service import email_sender_service

router = APIRouter()


@router.post("/send", response_model=EmailResponse)
async def send_email(request: EmailSendRequest):
    """
    Envoyer un email personnalise

    - **to_email**: Adresse email du destinataire
    - **subject**: Sujet de l'email
    - **body**: Corps du message (texte ou HTML)
    - **is_html**: True si le body est en HTML (optionnel, defaut: False)
    """
    try:
        result = email_sender_service.send_email(
            to_email=request.to_email,
            subject=request.subject,
            body=request.body,
            is_html=request.is_html
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=EmailResponse)
async def send_test_email(request: EmailTestRequest):
    """
    Envoyer un email de test predefini

    - **to_email**: Adresse email du destinataire
    """
    try:
        result = email_sender_service.send_test_email(to_email=request.to_email)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
