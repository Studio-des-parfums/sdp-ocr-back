from datetime import datetime

from pydantic import BaseModel


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str | None = None


class DeviceRegisterResponse(BaseModel):
    id: int
    device_id: str
    device_name: str | None = None
    status: str = "pending"


class DeviceVerifyRequest(BaseModel):
    device_id: str


class DeviceVerifyResponse(BaseModel):
    authorized: bool
    device_id: str
    status: str | None = None


class DeviceRenameRequest(BaseModel):
    device_name: str


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: str | None = None
    registered_at: datetime
    last_seen_at: datetime | None = None
    status: str
    decided_at: datetime | None = None
