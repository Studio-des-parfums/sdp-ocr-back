from fastapi import APIRouter, HTTPException

from app.repositories import device_repository
from app.schemas.device_schemas import (
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    DeviceVerifyRequest,
    DeviceVerifyResponse,
    DeviceResponse,
)

router = APIRouter()


@router.post("/devices/register", response_model=DeviceRegisterResponse)
async def register_device(payload: DeviceRegisterRequest):
    device = device_repository.register_device(
        device_id=payload.device_id,
        device_name=payload.device_name,
    )
    if not device:
        raise HTTPException(status_code=500, detail="Erreur enregistrement appareil")
    return DeviceRegisterResponse(
        id=device["id"],
        device_id=device["device_id"],
        device_name=device.get("device_name"),
        status=device["status"],
    )


@router.post("/devices/verify", response_model=DeviceVerifyResponse)
async def verify_device(payload: DeviceVerifyRequest):
    device = device_repository.verify_device(payload.device_id)
    if not device:
        return DeviceVerifyResponse(
            authorized=False,
            device_id=payload.device_id,
            status=None,
        )
    return DeviceVerifyResponse(
        authorized=device["status"] == "approved",
        device_id=device["device_id"],
        status=device["status"],
    )


@router.get("/devices", response_model=list[DeviceResponse])
async def list_devices():
    devices = device_repository.get_all_devices()
    return [DeviceResponse(**d) for d in devices]


@router.patch("/devices/{device_id}/approve")
async def approve_device(device_id: int):
    ok = device_repository.approve_device(device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    return {"status": "approved"}


@router.patch("/devices/{device_id}/reject")
async def reject_device(device_id: int):
    ok = device_repository.reject_device(device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    return {"status": "rejected"}
